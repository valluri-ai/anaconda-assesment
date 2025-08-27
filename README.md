# Jupyter Notebook to Runt Event Log Converter

This is a Next.js application with a backend API endpoint that converts a standard `.ipynb` Jupyter Notebook file into a specific JSON event log format compatible with the Runt architecture.

## Features

* **File Upload Endpoint**: Exposes a `/api/import` route that accepts `.ipynb` files via `multipart/form-data`.

* **Sequential Event Generation**: Parses the notebook and creates a series of ordered events, treating the notebook as a log of actions.

* **Fractional Indexing**: Correctly positions cells in sequence using the `createCellBetween` helper function to ensure deterministic ordering.

* **Comprehensive Type Support**: Handles markdown cells, code cells, and various output types (streams, execute results, display data, and errors).

* **Robust Error Handling**: Provides clear JSON error messages for invalid file types, parsing failures, or missing files.

* **Unit Tested**: Core conversion logic is validated with a suite of unit tests using Jest.

## Project Structure

The project is organized to separate concerns, making the codebase clean and maintainable.

```
.
├── src/
│   ├── app/
│   │   └── api/
│   │       └── import/
│   │           └── route.ts         # The API endpoint logic
│   │
│   ├── lib/
│   │   ├── ipynb-converter.ts       # Main orchestrator class
│   │   └── event-generators.ts      # Creates individual event payloads
│   │
│   ├── schema/
│   │   └── mod.ts                   # Runt event schema definitions (user-provided)
│   │
│   ├── types/
│   │   └── notebook-types.ts        # TypeScript interfaces for .ipynb files
│   │
│   └── tests/
│       ├── ipynb-converter.test.ts  # Tests for the main converter
│       └── event-generators.test.ts # Tests for the event generators
│
├── jest.config.js                   # Jest test runner configuration
├── package.json
└── README.md

```

## Getting Started

Follow these steps to get the project running locally.

### 1. Prerequisites

* Node.js (v18 or later recommended)

* npm or yarn

### 2. Installation

Clone the repository and install the required dependencies.

```
git clone <your-repository-url>
cd <repository-name>
npm install

```

### 3. Add the Runt Schema

This project requires the Runt schema definitions. **Manually copy** your `mod.ts` file (and any other related files) into the `src/schema/` directory.

### 4. Run the Development Server

Start the Next.js development server.

```
npm run dev

```

The application will be running at `http://localhost:3000`.

## API Usage

To convert a notebook, send a `POST` request to the `/api/import` endpoint.

* **URL**: `http://localhost:3000/api/import`

* **Method**: `POST`

* **Body**: `multipart/form-data`

* **Field**:

  * `notebook`: The `.ipynb` file to be converted.

### Example cURL Command

Replace `/path/to/your/notebook.ipynb` with the actual file path on your machine.

```
curl -X POST \
  http://localhost:3000/api/import \
  -F 'notebook=@/path/to/your/notebook.ipynb'

```

A successful request will return a `200 OK` status with the JSON event log as the response body.

## Running Tests

The project includes a suite of unit tests for the core logic. To run them, use the following command:

```
npm test

```

This will execute all test files located in the `src/tests/` directory and provide a summary of the results.
