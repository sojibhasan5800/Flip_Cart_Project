'use client'; // For Next.js client-side rendering

import { useState, useCallback } from 'react';
import ImageKit from 'imagekit-javascript'; // Import ImageKit JS SDK
import AxiosInstance from '../api/AxiosInstance'; // Your Axios instance for backend calls

export const useImageKitUpload = () => {
  // State for uploaded URL
  const [url, setUrl] = useState('');
  // State for loading status
  const [loading, setLoading] = useState(false);
  // State for errors
  const [error, setError] = useState(null);
  // State for upload progress (0-100)
  const [progress, setProgress] = useState(0);

  // Function to fetch authentication parameters from backend
  const getAuthParams = useCallback(async () => {
    try {
      const { data } = await AxiosInstance.get('/api/accounts/imagekit-token/'); // Call your backend endpoint
      return data; // Returns { token, signature, expire, publicKey }
    } catch (err) {
      throw new Error('Failed to get authentication: ' + err.message);
    }
  }, []);

  // Function to upload file to ImageKit
  const uploadFile = useCallback(async (file, options = {}) => {
    if (!file) {
      setError('No file selected');
      return;
    }

    setLoading(true); // Start loading
    setError(null); // Clear previous errors
    setProgress(0); // Reset progress
    setUrl(''); // Clear previous URL

    try {
      // Validate file (industry best practice: size and type limits)
      if (file.size > 10 * 1024 * 1024) { // Limit to 10MB
        throw new Error('File is too large (max 10MB)');
      }
      if (!file.type.startsWith('image/')) { // Allow only images
        throw new Error('Only image files are allowed');
      }

      // Get auth params from backend
      const authParams = await getAuthParams();
      const { token, signature, expire } = authParams;

      // Initialize ImageKit SDK with public key and URL endpoint
      const ik = new ImageKit({
        publicKey: authParams.publicKey,
        urlEndpoint: 'https://ik.imagekit.io/ehdyydeuq', // Your ImageKit URL endpoint from settings
      });

      // Upload the file
      const response = await ik.upload({
        file, // File object
        fileName: file.name, // File name
        token, // Auth token
        signature, // Signature
        expire, // Expiration time
        folder: options.folder || '/stores/', // Optional folder
        tags: options.tags || ['store_logo'], // Optional tags
        useUniqueFileName: true, // Avoid file name conflicts
        isPrivateFile: false, // Public file; set to true for private
      });

      // Set the uploaded URL
      setUrl(response.url);
      return response.url; // Return URL for use in component
    } catch (err) {
      setError(err.message); // Set error message
      console.error('Upload error:', err);
      throw err; // Throw error for component to handle
    } finally {
      setLoading(false); // End loading
    }
  }, [getAuthParams]);

  // Function to cancel upload (optional: can be expanded with AbortController if needed)
  const cancelUpload = useCallback(() => {
    setLoading(false);
    setError('Upload cancelled');
  }, []);

  // Return hook values and functions
  return { uploadFile, url, loading, error, progress, cancelUpload };
};