#!/bin/bash

# --- Project Setup Script for IPYNB to Event Log Converter ---

echo "🚀 Starting project setup..."

# 1. Create the main source directories
mkdir -p src/pages/api
mkdir -p src/lib
mkdir -p src/schema
mkdir -p src/types
mkdir -p src/tests

echo "✅ Created primary directories: pages, lib, schema, types, tests"

# 2. Create the TypeScript files
touch src/pages/api/convert-notebook.ts
touch src/lib/ipynb-converter.ts
touch src/lib/event-generators.ts
touch src/types/notebook-types.ts
touch src/tests/event-generators.test.ts

echo "✅ Created all necessary TypeScript files."

# 3. Populate the type definition file (notebook-types.ts)
cat <<EOL > src/types/notebook-types.ts
/**
 * @file Contains all TypeScript interfaces for representing the structure
 * of a standard Jupyter Notebook (.ipynb) file.
 */

export interface INotebook {
  cells: ICell[];
  metadata: {
    kernelspec?: {
      display_name: string;
      language: string;
      name: string;
    };
    language_info?: {
      name: string;
      version: string;
    };
    [key: string]: any;
  };
  nbformat: number;
  nbformat_minor: number;
}

export type ICell = IMarkdownCell | ICodeCell | IRawCell;

export interface IBaseCell {
  cell_type: 'markdown' | 'code' | 'raw';
  source: string | string[];
  metadata: Record<string, any>;
}

export interface IMarkdownCell extends IBaseCell {
  cell_type: 'markdown';
}

export interface IRawCell extends IBaseCell {
  cell_type: 'raw';
}

export interface ICodeCell extends IBaseCell {
  cell_type: 'code';
  execution_count: number | null;
  outputs: IOutput[];
}

export type IOutput = IStream | IExecuteResult | IDisplayData | IError;

export interface IStream {
  output_type: 'stream';
  name: 'stdout' | 'stderr';
  text: string | string[];
}

export interface IExecuteResult {
  output_type: 'execute_result';
  execution_count: number | null;
  metadata: Record<string, any>;
  data: {
    'text/plain'?: string | string[];
    'text/html'?: string | string[];
    'image/png'?: string;
    'application/json'?: any;
    [mimeType: string]: any;
  };
}

export interface IDisplayData {
  output_type: 'display_data';
  metadata: Record<string, any>;
  data: {
    'text/plain'?: string | string[];
    'text/html'?: string | string[];
    'image/png'?: string;
    'application/json'?: any;
    [mimeType: string]: any;
  };
}

export interface IError {
  output_type: 'error';
  ename: string;
  evalue: string;
  traceback: string[];
}
EOL

echo "✅ Populated notebook-types.ts."

# 4. Populate the event generators file (event-generators.ts)
cat <<EOL > src/lib/event-generators.ts
/**
 * @file This module is responsible for generating specific event payloads
 * based on the Runt event schema. It acts as a bridge between the raw
 * .ipynb format and the structured event log, encapsulating all direct
 * interactions with the schema definitions.
 */

import { v4 as uuidv4 } from 'uuid';
import {
  events,
  createCellBetween,
  CellReference,
  CellType,
  CellOperationResult,
} from '../schema/mod';
import {
  INotebook,
  IOutput,
  ICell,
} from '../types/notebook-types';

export type NotebookEvent = {
  name: string;
  args: Record<string, any>;
};

export function createActorProfileSetEvent(
  actorId: string,
  displayName: string,
): NotebookEvent {
  return events.actorProfileSet({
    id: actorId,
    type: 'human',
    displayName: displayName,
  });
}

export function createNotebookMetadataEvents(
  metadata: INotebook['metadata'],
): NotebookEvent[] {
  const metadataEvents: NotebookEvent[] = [];
  const title = \`Imported Notebook - \${new Date().toLocaleDateString()}\`;

  metadataEvents.push(events.notebookTitleChanged({ title }));

  if (metadata.kernelspec?.display_name) {
    metadataEvents.push(events.notebookMetadataSet({
      key: 'kernelspec_display_name',
      value: metadata.kernelspec.display_name,
    }));
  }
  if (metadata.kernelspec?.language) {
    metadataEvents.push(events.notebookMetadataSet({
      key: 'language',
      value: metadata.kernelspec.language,
    }));
  }

  return metadataEvents;
}

export function createCellCreatedEvent(
  cell: ICell,
  createdBy: string,
  cellBefore: CellReference | null,
  allCells: readonly CellReference[],
): CellOperationResult {
  const cellType: CellType = cell.cell_type === 'code' ? 'code' : 'markdown';
  
  const cellData = {
    id: \`cell-\${uuidv4()}\`,
    cellType: cellType,
    createdBy: createdBy,
  };

  return createCellBetween(cellData, cellBefore, null, allCells);
}

export function createCellSourceChangedEvent(
  cellId: string,
  source: string | string[],
  modifiedBy: string,
): NotebookEvent {
  const fullSource = Array.isArray(source) ? source.join('') : source;
  
  return events.cellSourceChanged({
    id: cellId,
    source: fullSource,
    modifiedBy: modifiedBy,
  });
}

export function createCellOutputEvents(
  cellId: string,
  outputs: IOutput[],
  clearedBy: string,
): NotebookEvent[] {
  if (!outputs || outputs.length === 0) {
    return [];
  }

  const outputEvents: NotebookEvent[] = [];

  outputEvents.push(events.cellOutputsCleared({
    cellId: cellId,
    wait: false,
    clearedBy: clearedBy,
  }));

  outputs.forEach((output, index) => {
    const outputId = \`output-\${uuidv4()}\`;
    
    switch (output.output_type) {
      case 'stream':
        outputEvents.push(events.terminalOutputAdded({
          id: outputId,
          cellId: cellId,
          position: index,
          streamName: output.name,
          content: {
            type: 'inline',
            data: Array.isArray(output.text) ? output.text.join('') : output.text,
          },
        }));
        break;

      case 'execute_result':
      case 'display_data':
        const representations = Object.entries(output.data).reduce((acc, [mimeType, data]) => {
          acc[mimeType] = { type: 'inline', data };
          return acc;
        }, {} as Record<string, { type: 'inline'; data: any }>);

        if (output.output_type === 'execute_result') {
            outputEvents.push(events.multimediaResultOutputAdded({
                id: outputId,
                cellId: cellId,
                position: index,
                representations: representations,
                executionCount: output.execution_count ?? 0,
            }));
        } else {
            outputEvents.push(events.multimediaDisplayOutputAdded({
                id: outputId,
                cellId: cellId,
                position: index,
                representations: representations,
            }));
        }
        break;

      case 'error':
        outputEvents.push(events.errorOutputAdded({
          id: outputId,
          cellId: cellId,
          position: index,
          content: {
            type: 'inline',
            data: {
              ename: output.ename,
              evalue: output.evalue,
              traceback: output.traceback,
            },
          },
        }));
        break;
    }
  });

  return outputEvents;
}
EOL

echo "✅ Populated event-generators.ts."

# 5. Initialize Git and make the first commit
echo "📦 Initializing Git repository..."
git init
git add .
git commit -m "feat: Initial project structure and event generators"
echo "✅ Git repository initialized and first commit made."


# Final instructions for the user
echo ""
echo "------------------------------------------------------------------"
echo "‼️ IMPORTANT NEXT STEPS:"
echo "1. Manually copy your entire 'schema' folder (containing mod.ts)"
echo "   into the 'src/schema/' directory that was just created."
echo ""
echo "2. Create a repository on a platform like GitHub and run the"
echo "   following commands to push your code:"
echo ""
echo "   git remote add origin YOUR_REPOSITORY_URL.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo "------------------------------------------------------------------"
echo ""
echo "🎉 Project structure is ready! You can now proceed with writing tests."
