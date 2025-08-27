import fs from 'fs';
import path from 'path';
// Mock schema before importing the converter to avoid ESM issues from dependencies
jest.mock('../schema/mod', () => {
  const events = {
    actorProfileSet: (args: any) => ({ name: 'v1.ActorProfileSet', args }),
    notebookTitleChanged: (args: any) => ({ name: 'v1.NotebookTitleChanged', args }),
    notebookMetadataSet: (args: any) => ({ name: 'v1.NotebookMetadataSet', args }),
    cellCreated2: (args: any) => ({ name: 'v2.CellCreated', args }),
    cellSourceChanged: (args: any) => ({ name: 'v1.CellSourceChanged', args }),
    terminalOutputAdded: (args: any) => ({ name: 'v1.TerminalOutputAdded', args }),
    multimediaResultOutputAdded: (args: any) => ({ name: 'v1.MultimediaResultOutputAdded', args }),
    multimediaDisplayOutputAdded: (args: any) => ({ name: 'v1.MultimediaDisplayOutputAdded', args }),
    errorOutputAdded: (args: any) => ({ name: 'v1.ErrorOutputAdded', args }),
    cellOutputsCleared: (args: any) => ({ name: 'v1.CellOutputsCleared', args }),
  };

  function createCellBetween(
    cellData: { id: string; cellType: 'code' | 'markdown'; createdBy: string },
    _cellBefore: any,
    _cellAfter: any,
    _allCells: any[],
  ) {
    const fractionalIndex = 'a0';
    return {
      events: [events.cellCreated2({ ...cellData, fractionalIndex })],
      newCellId: cellData.id,
      needsRebalancing: false,
    };
  }

  return { events, createCellBetween };
});

const { IpynbConverter } = require('../lib/ipynb-converter');
import { INotebook } from '../types/notebook-types';

describe('IpynbConverter integration with sample.ipynb', () => {
  it('produces expected sequence of events', () => {
    const samplePath = path.join(process.cwd(), 'sample.ipynb');
    const raw = fs.readFileSync(samplePath, 'utf-8');
    const notebook = JSON.parse(raw) as INotebook;

    const converter = new IpynbConverter(notebook);
    const events = converter.generateEvents();

    expect(events.length).toBeGreaterThanOrEqual(3);

    // First event is actor profile set
    expect(events[0].name).toBe('v1.ActorProfileSet');

    // There should be a v2.CellCreated event somewhere
    const created = events.find(e => e.name === 'v2.CellCreated');
    expect(created).toBeDefined();

    // There should be at least one source change event
    const sourceChanged = events.find(e => e.name === 'v1.CellSourceChanged');
    expect(sourceChanged).toBeDefined();
  });
});


