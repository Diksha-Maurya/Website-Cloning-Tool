// Add 'use client' at the top
'use client';

import Image from "next/image"; // You can keep this if you want the Next.js logo, or remove it.
import { useState } from 'react'; // Import useState

export default function Home() {
  // Add your state variables
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
    setClonedHtml(''); // Clear previous preview

    try {
      // Replace with your actual backend API endpoint URL
      const response = await fetch('http://localhost:8000/clone_website', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        // Ensure this body structure matches what your backend expects
        body: JSON.stringify({ target_url: url }),
      });

      if (!response.ok) {
        const errorData = await response.json(); // Or response.text() if not JSON
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      // Ensure this data access matches your backend's response structure
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
    // You can adjust the outer div's classes if needed, or keep them.
    // The classes like `grid`, `min-h-screen`, `p-8` are for layout and padding.
    <div className="grid grid-rows-[auto_1fr_auto] items-center justify-items-center min-h-screen p-8 pb-20 gap-16 sm:p-20 font-[family-name:var(--font-geist-sans)]">
      <main className="flex flex-col gap-8 row-start-2 items-center w-full max-w-4xl"> {/* Adjusted gap and width */}
        {/* You can keep the Next.js logo or remove it */}
        {/* <Image
          className="dark:invert mb-8" // Added margin-bottom
          src="/next.svg"
          alt="Next.js logo"
          width={180}
          height={38}
          priority
        /> */}

        <h1 className="text-3xl sm:text-4xl font-bold mb-8">Website Cloning Tool 🤖</h1> {/* Added a title */}

        {/* Your UI elements */}
        <div className="flex flex-col sm:flex-row gap-4 mb-8 w-full justify-center"> {/* Added margin-bottom and full width */}
          <input
            type="url"
            value={url}
            onChange={handleUrlChange}
            placeholder="https://example.com"
            // Tailwind classes for styling the input
            className="flex-grow appearance-none block w-full bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 border border-gray-300 dark:border-gray-600 rounded py-3 px-4 leading-tight focus:outline-none focus:bg-white dark:focus:bg-gray-800 focus:border-blue-500"
          />
          <button
            onClick={handleCloneClick}
            disabled={isLoading}
            // Tailwind classes for styling the button
            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded focus:outline-none focus:shadow-outline disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
          >
            {isLoading ? 'Cloning...' : 'Clone Website'}
          </button>
        </div>

        <h2 className="text-2xl font-semibold mb-4 self-start">Preview:</h2> {/* Added margin-bottom and self-start */}
        {isLoading && <p className="text-lg">Loading preview...</p>}
        <div
          style={{ /* Basic inline styles for dimensions and border */
            border: '1px solid #ccc',
            padding: '10px',
            minHeight: '400px', // Increased minHeight
            width: '100%',       // Take full width of the main container
            backgroundColor: '#f9f9f9',
            overflow: 'auto',
          }}
          // Using Tailwind for dark mode background on the preview itself
          className="dark:bg-gray-800 dark:border-gray-600"
          dangerouslySetInnerHTML={{ __html: clonedHtml }}
        />

        {/* You can remove or keep the Vercel/Next.js links below if you wish */}
        {/* <div className="flex gap-4 items-center flex-col sm:flex-row mt-12">
          ... existing links ...
        </div> */}
      </main>

      {/* The footer can be kept or modified/removed */}
      <footer className="row-start-3 flex gap-6 flex-wrap items-center justify-center mt-12">
        {/* ... existing footer links ... */}
        <p className="text-sm text-gray-500 dark:text-gray-400">Orchids SWE Intern Challenge</p>
      </footer>
    </div>
  );
}