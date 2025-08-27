/**
 * @file Next.js API Route for converting an .ipynb file to a Runt event log.
 * This endpoint handles multipart/form-data requests containing the notebook file.
 */

import { NextResponse } from 'next/server';
import { IpynbConverter } from '@/lib/ipynb-converter'; // Using alias for cleaner imports
import { INotebook } from '@/types/notebook-types';
import { getStorageAdapter } from '@/lib/storage';

export const runtime = 'nodejs';

/**
 * Handles POST requests to /api/import.
 * Expects a multipart/form-data request with a single file field named 'notebook'.
 *
 * @param {Request} request The incoming HTTP request.
 * @returns A NextResponse object with the JSON event log or an error message.
 */
export async function POST(request: Request) {
  try {
    // 1. Get the form data from the request
    const formData = await request.formData();
    const file = formData.get('notebook') as File | null;

    // --- Robust Error Handling for File Upload ---
    if (!file) {
      return NextResponse.json(
        { error: "No file uploaded. Please include a file in the 'notebook' field." },
        { status: 400 } // Bad Request
      );
    }

    if (file.type !== 'application/json' && !file.name.endsWith('.ipynb')) {
        return NextResponse.json(
          { error: "Invalid file type. Please upload a valid .ipynb file." },
          { status: 400 } // Bad Request
        );
    }

    // 2. Read and parse the file content
    const fileContent = await file.text();
    let notebookJson: INotebook;

    try {
      notebookJson = JSON.parse(fileContent);
      // Basic validation to ensure it looks like a notebook file
      if (!notebookJson.cells || !notebookJson.nbformat) {
        throw new Error("Parsed JSON does not appear to be a valid notebook file.");
      }
    } catch (parseError) {
      console.error("JSON Parsing Error:", parseError);
      return NextResponse.json(
        { error: 'Failed to parse the uploaded file. Please ensure it is a valid JSON .ipynb file.' },
        { status: 400 } // Bad Request
      );
    }

    // 3. Instantiate the converter and generate events
    const converter = new IpynbConverter(notebookJson);
    const events = converter.generateEvents();

    // 4. Store via adapter
    const adapter = getStorageAdapter();
    const result = await adapter.saveEvents(events, {
      filenameBase: file.name?.replace(/\.[^.]+$/, '') || 'notebook-events',
    });

    // 5. Return the successful response with storage location
    return NextResponse.json({ events, stored: result }, { status: 200 });

  } catch (error) {
    // --- Catch-all for any other unexpected errors ---
    console.error('An unexpected error occurred:', error);
    return NextResponse.json(
      { error: 'An internal server error occurred during file processing.' },
      { status: 500 } // Internal Server Error
    );
  }
}
