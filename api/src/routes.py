import json
import os
from fastapi import APIRouter, Query
from pydantic import BaseModel
from openai import OpenAI
from anthropic import Anthropic
from typing import List, Optional, Dict, Any, Set

from clients.footway import FootwayClient, InventoryItem, PaginatedInventoryResponse
from clients.postgres import PostgresVectorClient
from utils import log

logger = log.get_logger(__name__)

router = APIRouter()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

chat_messages = [{"role": "system", "content": "You are a bratty helpful assistant."}]


#### Models ####

## Demo Endpoints ##

class Profile:
    def __init__(self):
        self.department: str = ''
        self.size: int = 0
        self.product_type: str = ''
        self.vectors: set[str] = set()
        self.products: List[InventoryItem] = []

profile = Profile()

class DemoRequest(BaseModel):
    prompt: str

class DemoResponse(BaseModel):
    message: str

## Footway ##

class InventorySearchResponse(BaseModel):
    items: List[InventoryItem]
    total_items: int
    current_page: int
    total_pages: int

## Vector Search ##

class VectorSearchItem(BaseModel):
    id: str
    name: str
    description: str
    similarity_score: float
    metadata: Dict[str, Any]

class VectorSearchResponse(BaseModel):
    items: List[VectorSearchItem]

class WhatWeWantResponse(BaseModel):
    message: DemoResponse
    inventory: PaginatedInventoryResponse | None

#### Routes ####

@router.get("/hello",
            response_model=DemoResponse,
            description="Returns a greeting message.")
async def hello() -> DemoResponse:
    return DemoResponse(message="Hello from the API!")

@router.post("/test/openai",
             response_model=DemoResponse,
             description="Makes a reqeust against OpenAI")
async def query_openai(request: DemoRequest) -> DemoResponse:
    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": request.prompt},
        ]
    )
    return DemoResponse(message=completion.choices[0].message.content)

@router.post("/filter/openai",
             response_model=WhatWeWantResponse,
             description="Makes a reqeust against OpenAI")
async def filter_openai(request: DemoRequest) -> WhatWeWantResponse:
    vectors = await search_vector_inventory(request.prompt)
    new_vectors = set(map(lambda v: v.id, vectors.items)).difference(profile.vectors)
    profile.vectors = profile.vectors.union(new_vectors)
    inventory = None if len(new_vectors) == 0 else await search_footway_inventory(None, None, None, list(new_vectors))
    if inventory != None:
        for item in inventory.items:
            profile.products.append(item)
    
    print("Here is the vectors", new_vectors)

      

    if inventory != None: chat_messages.append({"role": "system", "content": "Here is a json of available products based on the user's prompt; use this to be as helpful as possible: " + json.dumps([item.__dict__ for item in profile.products])})
    chat_messages.append({"role": "user", "content": request.prompt})
    
            #  {"role": "system", "content": "Show what it costs based on the available products" + json.dumps([item.__dict__ for item in inventory.items])} if inventory 
            #  else {"role": "system", "content": "Ask for more information on what the product the user is intrested in."},

    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=chat_messages
    )

    chat_messages.append({"role": "assistant", "content": completion.choices[0].message.content})

    print("here is the messages sent", len(chat_messages))

    return WhatWeWantResponse(message=DemoResponse(message=completion.choices[0].message.content), inventory=inventory)


@router.post("/test/anthropic",
             response_model=DemoResponse,
             description="Makes a request against Anthropic")
async def query_claude(request: DemoRequest) -> DemoResponse:
    messages = [{"role": "user", "content": request.prompt}]

    response = anthropic_client.messages.create(
        system="You are a helpful assistant.",
        model="claude-3-5-haiku-20241022",
        messages=messages,
        max_tokens=300,
        temperature=0.7,
    )
    return DemoResponse(message=response.content[0].text)

@router.get("/test/footway",
            response_model=InventorySearchResponse,
            description="Search Footway inventory")
async def search_footway_inventory(
    merchant_id: Optional[List[str]] = Query(None),
    product_name: Optional[str] = None,
    vendor: Optional[List[str]] = Query(None),
    variant_ids: Optional[List[str]] = Query(None),
    page: int = 1,
    page_size: int = 20
) -> InventorySearchResponse:
    footway_client = FootwayClient(api_key=os.getenv("FOOTWAY_API_KEY"))
    try:
        response = await footway_client.search_inventory(
            merchant_id=merchant_id,
            product_name=product_name,
            vendor=vendor,
            variant_ids=variant_ids,
            page=page,
            page_size=page_size
        )
        return response
    finally:
        await footway_client.close()

@router.get("/test/vector",
            response_model=VectorSearchResponse,
            description="Search inventory using vector similarity")
async def search_vector_inventory(
    query: str,
    page_size: int = 20
) -> VectorSearchResponse:
    # Initialize clients
    vector_client = PostgresVectorClient()

    try:
        # Get embedding for query using OpenAI
        embedding_response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=query
        )

        # Extract the embedding vector
        query_vector = embedding_response.data[0].embedding

        # Search vectors in PostgreSQL
        search_results = vector_client.search_vectors(
            query_vector=query_vector,
            limit=page_size
        )

        # Convert results to VectorSearchItems
        items = []
        for content, metadata, score in search_results:
            # Convert metadata from JSON string if needed
            if isinstance(metadata, str):
                metadata = json.loads(metadata)

            # Ensure id is converted to string
            item_id = str(metadata.get("id", ""))

            item = VectorSearchItem(
                id=item_id,  # Now guaranteed to be a string
                name=metadata.get("name", ""),
                description=content,
                similarity_score=float(score),  # Ensure score is float
                metadata=metadata
            )
            items.append(item)

        return VectorSearchResponse(
            items=items,
        )

    finally:
        vector_client.close()
