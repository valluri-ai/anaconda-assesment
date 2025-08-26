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
  const title = `Imported Notebook - ${new Date().toLocaleDateString()}`;

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
    id: `cell-${uuidv4()}`,
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
    const outputId = `output-${uuidv4()}`;
    
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
