import { ApiClientInterface } from '../types';
import mockResponse from './mockResponse.json';

export interface Item {
  merchantId: string;
  variantId: string;
  productName: string;
  quantity: number;
  supplierModelNumber: string;
  ean: string[];
  size: string;
  price: number;
  product_description: string;
  image_url: string;
}

export interface Inventory {
  items: Item[];
}

export interface Response {
  message: string | { message: string };
  inventory?: Inventory;
}

export interface Message {
  role: 'user' | 'bot';
  content: string;
  inventory?: Inventory;
}

const mockApiCall = (): Promise<Response> => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(mockResponse as unknown as Response);
    }, 1000);
  });
}

export function createChatApi(client: ApiClientInterface) {
  return {
    async sendMessage(prompt: string): Promise<Message> {
      const on_error = (messages: string[]) => {
        console.error('Error calling the API:', messages);
      };
      const response = await client.post<Response>('/api/filter/openai', on_error, { prompt });
      // const response = await mockApiCall();

      let message = response.message;

      if (typeof message === 'object') {
        message = message.message;
      }

      if (response.hasOwnProperty('inventory')) {
        return { role: 'bot', content: message, inventory: response.inventory };
      }

      return { role: 'bot', content: message as string };
    },
  };
}
