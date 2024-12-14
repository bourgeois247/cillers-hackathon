import React, { useState } from 'react';
import { ApiClientRest } from '../../../rest/api_client_rest'
import { createChatApi, Message } from '../../../rest/modules/chat'
import BeatLoader from "react-spinners/BeatLoader";

interface ItemsProps {
    client: ApiClientRest
}

const Chat: React.FC<ItemsProps> = ({ client }) => {
  const chatApi = createChatApi(client);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage: Message = { role: 'user', content: input.trim() };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');

    try {
      setLoading(true);
      const botMessage = await chatApi.sendMessage(userMessage.content);
      setLoading(false);
      setMessages((prev) => [...prev, botMessage]);
      console.log(botMessage);
    } catch (err) {
      console.error(err);
      setMessages((prev) => [
        ...prev,
        { role: 'bot', content: `Error: Unable to fetch response: ${err}` },
      ]);
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col">
      <div className="flex-1 p-4 overflow-y-auto">
        <div className="space-y-4 flex flex-col">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`p-3 rounded ${
                message.role === 'user'
                  ? 'bg-primary text-primary-content self-end'
                  : 'bg-base-200 text-gray-400'
              }`}
              style={{ maxWidth: '70%', alignSelf: message.role === 'user' ? 'flex-end' : 'flex-start' }}
            >
              {message.content}
              
              {message.inventory && message.inventory && (
                <div className="mt-2">
                <div className="grid grid-cols-3 gap-4">
                    {message.inventory.map((item) => (
                      <div key={`${item.productName}`} style={{ maxHeight: '26rem' }}>
                        <div className="rounded-t-lg" style={{
                          backgroundImage: `url(${item.image_url})`,
                          backgroundSize: 'cover',
                          backgroundRepeat: 'no-repeat',
                          height: '20rem'}}></div>
                        <div className='bg-white p-4 rounded-b-lg'>
                          <h2 className='font-bold text-gray-500'>{item.productName}</h2>
                          <h4>{item.price}</h4>
                          <div>{item.size}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>)}
            </div>
          ))}
          {isLoading && <div className='bg-base-200 p-3 rounded' style={{ maxWidth: '70%', alignSelf: 'flex-start' }}>
            <BeatLoader
              color={'#fff'}
              loading={isLoading}
              cssOverride={{}}
              size={10}
              aria-label="Loading Spinner"
              data-testid="loader"
            />
          </div>}
        </div>
      </div>
      <div className="p-4 bg-base-300">
        <div className="form-control">
          <div className="input-group flex">
            <input
              type="text"
              className="input flex-grow text-gray-400 mr-4"
              placeholder="Type your message..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
            />
            <button className="btn btn-primary" onClick={sendMessage}>
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Chat;
