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
