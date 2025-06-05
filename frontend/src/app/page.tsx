'use client';

import Image from "next/image"; 
import { useState } from 'react';

export default function Home() {
  const [url, setUrl] = useState<string>('');
  const [clonedHtml, setClonedHtml] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Add your handler functions
  const handleUrlChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setUrl(event.target.value);
  };

  const handleCloneClick = async () => {
    if (!url) {
      alert('Please enter a URL.');
      return;
    }
    setIsLoading(true);
    setClonedHtml('');

    try {
      const response = await fetch('http://localhost:8000/clone_website', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },

        body: JSON.stringify({ target_url: url }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setClonedHtml(data.cloned_html);

    } catch (error) {
      console.error("Failed to clone:", error);
      let errorMessage = "Error cloning website.";
      if (error instanceof Error) {
        errorMessage += ` Details: ${error.message}`;
      }
      setClonedHtml(`<p style="color: red;">${errorMessage}</p>`);
    } finally {
      setIsLoading(false);
    }
  };

  return (

    <div className="grid grid-rows-[auto_1fr_auto] items-center justify-items-center min-h-screen p-8 pb-20 gap-16 sm:p-20 font-[family-name:var(--font-geist-sans)]">
      <main className="flex flex-col gap-8 row-start-2 items-center w-full max-w-4xl"> {/* Adjusted gap and width */}
        {/* */}
        {/* \
         */}

        <h1 className="text-3xl sm:text-4xl font-bold mb-8">Website Cloning Tool 🤖</h1> {/* Added a title */}

        {/*  */}
        <div className="flex flex-col sm:flex-row gap-4 mb-8 w-full justify-center"> {/* Added margin-bottom and full width */}
          <input
            type="url"
            value={url}
            onChange={handleUrlChange}
            placeholder="https://example.com"
            className="flex-grow appearance-none block w-full bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 border border-gray-300 dark:border-gray-600 rounded py-3 px-4 leading-tight focus:outline-none focus:bg-white dark:focus:bg-gray-800 focus:border-blue-500"
          />
          <button
            onClick={handleCloneClick}
            disabled={isLoading}
            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded focus:outline-none focus:shadow-outline disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
          >
            {isLoading ? 'Cloning...' : 'Clone Website'}
          </button>
        </div>

        <h2 className="text-2xl font-semibold mb-4 self-start">Preview:</h2> {/*  */}
        {isLoading && <p className="text-lg">Loading preview...</p>}
        <div
          style={{ 
            border: '1px solid #ccc',
            padding: '10px',
            minHeight: '400px', 
            width: '100%',
            backgroundColor: '#f9f9f9',
            overflow: 'auto',
          }}
  
          className="dark:bg-gray-800 dark:border-gray-600"
          dangerouslySetInnerHTML={{ __html: clonedHtml }}
        />

        {/*  */}
        {/*  */}
      </main>

      {/*  */}
      <footer className="row-start-3 flex gap-6 flex-wrap items-center justify-center mt-12">
        {/* */}
        <p className="text-sm text-gray-500 dark:text-gray-400">Orchids SWE Intern Challenge</p>
      </footer>
    </div>
  );
}