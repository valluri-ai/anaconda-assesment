declare module 'next/server' {
  export const NextResponse: {
    json: (data: any, init?: { status?: number }) => any;
  };
}





