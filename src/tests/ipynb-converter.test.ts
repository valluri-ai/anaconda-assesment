/**
 * @file Unit tests for the IpynbConverter class.
 * The entire event-generators module is mocked to isolate the converter's
 * orchestration logic. We verify that the converter calls the correct
 * generator functions in the correct sequence.
 */

import { IpynbConverter } from '../lib/ipynb-converter';
import { INotebook, IMarkdownCell, ICodeCell, IOutput } from '../types/notebook-types';
import { CellReference } from '../schema/mod';

// --- Mock the entire event-generators module ---
// This is the key to testing the converter in isolation.
jest.mock('../lib/event-generators', () => ({
  createActorProfileSetEvent: jest.fn(() => ({ name: 'mockActorEvent', args: {} })),
  createNotebookMetadataEvents: jest.fn(() => [{ name: 'mockMetadataEvent', args: {} }]),
  createCellCreatedEvent: jest.fn(), // We'll provide specific mock implementations in tests
  createCellSourceChangedEvent: jest.fn(() => ({ name: 'mockSourceEvent', args: {} })),
  createCellOutputEvents: jest.fn(() => [{ name: 'mockOutputEvent', args: {} }]),
}));

// Import the mocked functions so we can spy on their calls.
const {
  createActorProfileSetEvent,
  createNotebookMetadataEvents,
  createCellCreatedEvent,
  createCellSourceChangedEvent,
  createCellOutputEvents,
} = require('../lib/event-generators');


// --- Test Suite ---

describe('IpynbConverter', () => {
  // Clear all mock function call histories before each test.
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // Test Case 1: Empty Notebook
  it('should only generate initial actor and metadata events for an empty notebook', () => {
    const emptyNotebook: INotebook = {
      cells: [],
      metadata: {},
      nbformat: 4,
      nbformat_minor: 5,
    };

    const converter = new IpynbConverter(emptyNotebook);
    converter.generateEvents();

    // Verify initial events were called
    expect(createActorProfileSetEvent).toHaveBeenCalledTimes(1);
    expect(createNotebookMetadataEvents).toHaveBeenCalledTimes(1);

    // Verify no cell-related events were called
    expect(createCellCreatedEvent).not.toHaveBeenCalled();
    expect(createCellSourceChangedEvent).not.toHaveBeenCalled();
    expect(createCellOutputEvents).not.toHaveBeenCalled();
  });

  // Test Case 2: Simple Notebook & `cellBefore` Logic
  it('should pass the correct `cellBefore` reference between cell creation calls', () => {
    const markdownCell: IMarkdownCell = { cell_type: 'markdown', source: '# Title', metadata: {} };
    const codeCell: ICodeCell = { cell_type: 'code', source: 'print("hi")', metadata: {}, execution_count: 1, outputs: [] };
    const simpleNotebook: INotebook = {
      cells: [markdownCell, codeCell],
      metadata: {},
      nbformat: 4,
      nbformat_minor: 5,
    };

    // Mock the return values of createCellCreatedEvent to simulate the real process
    const mockCellRef1: CellReference = { id: 'cell-1', cellType: 'markdown', fractionalIndex: 'a0' };
    const mockCellRef2: CellReference = { id: 'cell-2', cellType: 'code', fractionalIndex: 'a5' };

    (createCellCreatedEvent as jest.Mock)
      .mockReturnValueOnce({ events: [{ name: 'v2.CellCreated', args: { fractionalIndex: 'a0' } }], newCellId: 'cell-1' })
      .mockReturnValueOnce({ events: [{ name: 'v2.CellCreated', args: { fractionalIndex: 'a5' } }], newCellId: 'cell-2' });

    const converter = new IpynbConverter(simpleNotebook);
    converter.generateEvents();

    // Verify that the creation function was called for each cell
    expect(createCellCreatedEvent).toHaveBeenCalledTimes(2);

    // *** CRITICAL TEST for fractional indexing ***
    // Check the arguments of each call to ensure `cellBefore` was passed correctly.
    const calls = (createCellCreatedEvent as jest.Mock).mock.calls;

    // First call: `cellBefore` should be null
    expect(calls[0][2]).toBeNull();

    // Second call: `cellBefore` should be the reference of the first cell
    expect(calls[1][2]).toEqual(mockCellRef1);

    // Verify other functions were called correctly
    expect(createCellSourceChangedEvent).toHaveBeenCalledTimes(2);
    expect(createCellSourceChangedEvent).toHaveBeenCalledWith('cell-1', markdownCell.source, expect.any(String));
    expect(createCellSourceChangedEvent).toHaveBeenCalledWith('cell-2', codeCell.source, expect.any(String));
  });

  // Test Case 3: Comprehensive Outputs
  it('should call createCellOutputEvents with all outputs for a code cell', () => {
    const mockOutputs: IOutput[] = [
        { output_type: 'stream', name: 'stdout', text: 'Hello' },
        { output_type: 'execute_result', execution_count: 1, data: { 'text/plain': '1' }, metadata: {} },
        { output_type: 'error', ename: 'Error', evalue: 'Fail', traceback: [] }
    ];
    const codeCellWithOutputs: ICodeCell = {
        cell_type: 'code',
        source: 'complex_code()',
        metadata: {},
        execution_count: 1,
        outputs: mockOutputs,
    };
    const notebook: INotebook = {
        cells: [codeCellWithOutputs],
        metadata: {},
        nbformat: 4,
        nbformat_minor: 5,
    };

    // Mock the creation event to return a predictable ID
    (createCellCreatedEvent as jest.Mock).mockReturnValueOnce({
        events: [{ name: 'v2.CellCreated', args: { fractionalIndex: 'a0' } }],
        newCellId: 'complex-cell-id',
    });

    const converter = new IpynbConverter(notebook);
    converter.generateEvents();

    // Verify that the output generator was called once
    expect(createCellOutputEvents).toHaveBeenCalledTimes(1);

    // Verify it was called with the correct cell ID and the full, original array of outputs
    expect(createCellOutputEvents).toHaveBeenCalledWith(
        'complex-cell-id',
        mockOutputs,
        expect.any(String)
    );
  });
});
