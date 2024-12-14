import React from 'react';
import Demo from './demos/rest/Demo';

const Main: React.FC = () => {
  const component: React.ReactElement = (() => {
    return (
      <main className="min-h-screen flex flex-col">
        <Demo/>
      </main>
    )
  })();
  return component;
}

export default Main;
