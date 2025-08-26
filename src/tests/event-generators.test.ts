/**
 * @file Unit tests for the event-generators module.
 * We mock the schema module to isolate our generator logic and verify
 * that the correct event creation functions are called with the correct arguments.
 */

import {
    createActorProfileSetEvent,
    createNotebookMetadataEvents,
    createCellCreatedEvent,
    createCellSourceChangedEvent,
    createCellOutputEvents,
  } from '../lib/event-generators';
  import { ICell, ICodeCell, IMarkdownCell, INotebook, IOutput } from '../types/notebook-types';
  import { CellReference } from '../schema/mod';
  
  // --- Mocking the Schema Module ---
  // We replace the actual schema functions with Jest mock functions.
  // This allows us to check *if* and *how* they are called by our generators.
  jest.mock('../schema/mod', () => ({
    events: {
      actorProfileSet: jest.fn(args => ({ name: 'v1.ActorProfileSet', args })),
      notebookTitleChanged: jest.fn(args => ({ name: 'v1.NotebookTitleChanged', args })),
      notebookMetadataSet: jest.fn(args => ({ name: 'v1.NotebookMetadataSet', args })),
      cellSourceChanged: jest.fn(args => ({ name: 'v1.CellSourceChanged', args })),
      cellOutputsCleared: jest.fn(args => ({ name: 'v1.CellOutputsCleared', args })),
      terminalOutputAdded: jest.fn(args => ({ name: 'v1.TerminalOutputAdded', args })),
      multimediaResultOutputAdded: jest.fn(args => ({ name: 'v1.MultimediaResultOutputAdded', args })),
      multimediaDisplayOutputAdded: jest.fn(args => ({ name: 'v1.MultimediaDisplayOutputAdded', args })),
      errorOutputAdded: jest.fn(args => ({ name: 'v1.ErrorOutputAdded', args })),
    },
    createCellBetween: jest.fn((cellData, _before, _after, _all) => ({
      events: [{
        name: 'v2.CellCreated',
        args: { ...cellData, fractionalIndex: 'mockFractionalIndex' }
      }],
      newCellId: cellData.id,
      needsRebalancing: false,
    })),
  }));
  
  // We need to import the mocked functions to spy on them in our tests.
  const { events, createCellBetween } = require('../schema/mod');
  
  // --- Test Suite ---
  
  describe('Event Generators', () => {
    const actorId = 'user-uuid-123';
  
    // Clear mock history before each test to ensure a clean state.
    beforeEach(() => {
      jest.clearAllMocks();
    });
  
    // --- Tests for createActorProfileSetEvent ---
    describe('createActorProfileSetEvent', () => {
      it('should generate a valid ActorProfileSet event', () => {
        const displayName = 'Test User';
        const event = createActorProfileSetEvent(actorId, displayName);
  
        expect(event.name).toBe('v1.ActorProfileSet');
        expect(events.actorProfileSet).toHaveBeenCalledWith({
          id: actorId,
          type: 'human',
          displayName: displayName,
        });
      });
    });
  
    // --- Tests for createNotebookMetadataEvents ---
    describe('createNotebookMetadataEvents', () => {
      it('should create a title and kernelspec events', () => {
        const mockMetadata: INotebook['metadata'] = {
          kernelspec: {
            display_name: 'Python 3',
            language: 'python',
            name: 'python3',
          },
        };
        const metadataEvents = createNotebookMetadataEvents(mockMetadata);
  
        expect(metadataEvents.length).toBe(3);
        expect(events.notebookTitleChanged).toHaveBeenCalled();
        expect(events.notebookMetadataSet).toHaveBeenCalledWith({
          key: 'kernelspec_display_name',
          value: 'Python 3',
        });
        expect(events.notebookMetadataSet).toHaveBeenCalledWith({
          key: 'language',
          value: 'python',
        });
      });
    });
  
    // --- Tests for createCellCreatedEvent ---
    describe('createCellCreatedEvent', () => {
      it('should call createCellBetween with correct markdown cell data', () => {
        const mockCell: IMarkdownCell = { cell_type: 'markdown', source: '# Hello', metadata: {} };
        createCellCreatedEvent(mockCell, actorId, null, []);
  
        expect(createCellBetween).toHaveBeenCalledWith(
          expect.objectContaining({
            cellType: 'markdown',
            createdBy: actorId,
          }),
          null,
          null,
          []
        );
      });
  
      it('should call createCellBetween with correct code cell data', () => {
          const mockCell: ICodeCell = { cell_type: 'code', source: 'print("hi")', metadata: {}, execution_count: 1, outputs: [] };
          createCellCreatedEvent(mockCell, actorId, null, []);
    
          expect(createCellBetween).toHaveBeenCalledWith(
            expect.objectContaining({
              cellType: 'code',
              createdBy: actorId,
            }),
            null,
            null,
            []
          );
        });
    });
  
    // --- Tests for createCellSourceChangedEvent ---
    describe('createCellSourceChangedEvent', () => {
      const cellId = 'cell-uuid-456';
      it('should handle a string source correctly', () => {
        const source = 'print("Hello, World!")';
        createCellSourceChangedEvent(cellId, source, actorId);
        expect(events.cellSourceChanged).toHaveBeenCalledWith({
          id: cellId,
          source: source,
          modifiedBy: actorId,
        });
      });
  
      it('should join an array of strings for the source', () => {
        const source = ['line 1\n', 'line 2'];
        createCellSourceChangedEvent(cellId, source, actorId);
        expect(events.cellSourceChanged).toHaveBeenCalledWith({
          id: cellId,
          source: 'line 1\nline 2',
          modifiedBy: actorId,
        });
      });
    });
  
    // --- Tests for createCellOutputEvents (Comprehensive) ---
    describe('createCellOutputEvents', () => {
      const cellId = 'cell-uuid-789';
  
      it('should return an empty array if there are no outputs', () => {
        const outputEvents = createCellOutputEvents(cellId, [], actorId);
        expect(outputEvents).toEqual([]);
      });
  
      it('should always start with a CellOutputsCleared event', () => {
          const mockOutputs: IOutput[] = [{ output_type: 'stream', name: 'stdout', text: 'hi' }];
          const outputEvents = createCellOutputEvents(cellId, mockOutputs, actorId);
          expect(outputEvents[0].name).toBe('v1.CellOutputsCleared');
          expect(events.cellOutputsCleared).toHaveBeenCalledWith({
              cellId,
              wait: false,
              clearedBy: actorId
          });
      });
  
      it('should correctly generate a stream output event', () => {
          const mockOutputs: IOutput[] = [{ output_type: 'stream', name: 'stdout', text: 'Hello Stream' }];
          createCellOutputEvents(cellId, mockOutputs, actorId);
          expect(events.terminalOutputAdded).toHaveBeenCalledWith(expect.objectContaining({
              cellId,
              streamName: 'stdout',
              content: { type: 'inline', data: 'Hello Stream' }
          }));
      });
  
      it('should correctly generate an execute_result event', () => {
          const mockOutputs: IOutput[] = [{
              output_type: 'execute_result',
              execution_count: 1,
              metadata: {},
              data: { 'text/plain': 'Result', 'text/html': '<p>Result</p>' }
          }];
          createCellOutputEvents(cellId, mockOutputs, actorId);
          expect(events.multimediaResultOutputAdded).toHaveBeenCalledWith(expect.objectContaining({
              cellId,
              executionCount: 1,
              representations: {
                  'text/plain': { type: 'inline', data: 'Result' },
                  'text/html': { type: 'inline', data: '<p>Result</p>' }
              }
          }));
      });
  
      it('should correctly generate an error output event', () => {
          const mockOutputs: IOutput[] = [{
              output_type: 'error',
              ename: 'ValueError',
              evalue: 'An error occurred',
              traceback: ['line 1', 'line 2']
          }];
          createCellOutputEvents(cellId, mockOutputs, actorId);
          expect(events.errorOutputAdded).toHaveBeenCalledWith(expect.objectContaining({
              cellId,
              content: {
                  type: 'inline',
                  data: {
                      ename: 'ValueError',
                      evalue: 'An error occurred',
                      traceback: ['line 1', 'line 2']
                  }
              }
          }));
      });
    });
  });
  