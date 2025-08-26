/**
 * @file This module contains the main IpynbConverter class, which orchestrates
 * the entire process of converting a parsed .ipynb file into a Runt event log.
 */

import { v4 as uuidv4 } from 'uuid';
import { INotebook, ICodeCell } from '../types/notebook-types';
import { CellReference } from '../schema/mod';
import {
  NotebookEvent,
  createActorProfileSetEvent,
  createNotebookMetadataEvents,
  createCellCreatedEvent,
  createCellSourceChangedEvent,
  createCellOutputEvents,
} from './event-generators';

/**
 * Orchestrates the conversion of a Jupyter Notebook JSON object into a
 * structured event log.
 */
export class IpynbConverter {
  private readonly notebook: INotebook;
  private readonly actorId: string;
  private events: NotebookEvent[] = [];
  private cellReferences: CellReference[] = [];

  /**
   * Initializes the converter with the notebook data.
   * @param notebook The parsed JSON content of an .ipynb file.
   */
  constructor(notebook: INotebook) {
    this.notebook = notebook;
    // Each import session is performed by a new, unique actor.
    this.actorId = `user-${uuidv4()}`;
  }

  /**
   * Generates the complete, ordered list of events from the notebook.
   * This is the main entry point for the conversion process.
   * @returns An array of NotebookEvent objects.
   */
  public generateEvents(): NotebookEvent[] {
    this._generateInitialEvents();
    this._generateCellEvents();
    return this.events;
  }

  /**
   * Creates the initial events that set up the actor profile and notebook metadata.
   */
  private _generateInitialEvents(): void {
    // 1. Create an actor profile for the user performing the import.
    const actorEvent = createActorProfileSetEvent(this.actorId, 'Notebook Importer');
    this.events.push(actorEvent);

    // 2. Create events for the notebook's metadata (e.g., title, language).
    const metadataEvents = createNotebookMetadataEvents(this.notebook.metadata);
    this.events.push(...metadataEvents);
  }

  /**
   * Iterates through each cell in the notebook and generates the corresponding
   * creation, source, and output events in the correct sequence.
   */
  private _generateCellEvents(): void {
    // This variable will hold the reference to the previously processed cell,
    // which is crucial for the fractional indexing logic.
    let cellBefore: CellReference | null = null;

    for (const cell of this.notebook.cells) {
      // 1. Generate the 'CellCreated' event. This helper function returns
      // not just the event but also the newly created cell's ID.
      const creationResult = createCellCreatedEvent(
        cell,
        this.actorId,
        cellBefore,
        this.cellReferences
      );
      
      this.events.push(...creationResult.events);
      const newCellId = creationResult.newCellId;

      // 2. Generate the 'CellSourceChanged' event to populate the cell's content.
      const sourceEvent = createCellSourceChangedEvent(
        newCellId,
        cell.source,
        this.actorId
      );
      this.events.push(sourceEvent);

      // 3. If it's a code cell, generate its output events.
      if (cell.cell_type === 'code') {
        const codeCell = cell as ICodeCell;
        const outputEvents = createCellOutputEvents(
          newCellId,
          codeCell.outputs,
          this.actorId
        );
        this.events.push(...outputEvents);
      }

      // 4. Update our references for the next iteration.
      // We find the newly created cell's event to get its fractionalIndex.
      const createdEvent = creationResult.events.find(e => e.name === 'v2.CellCreated');
      const newCellRef: CellReference = {
        id: newCellId,
        // The cellType here must match the one used in the event schema.
        cellType: cell.cell_type === 'code' ? 'code' : 'markdown',
        fractionalIndex: createdEvent?.args.fractionalIndex || null,
      };

      this.cellReferences.push(newCellRef);
      cellBefore = newCellRef; // Set `cellBefore` for the next loop iteration.
    }
  }
}
