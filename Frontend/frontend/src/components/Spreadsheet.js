import React from 'react';
import { DataGrid } from '@mui/x-data-grid';

function Spreadsheet({ data }) {
  const columns = [
    { field: 'Date', headerName: 'Date', width: 150 },
    { field: 'Description', headerName: 'Description', width: 300 },
    { field: 'Deposit Amount', headerName: 'Deposit Amount', width: 150, type: 'number' },
    { field: 'Withdrawal Amount', headerName: 'Withdrawal Amount', width: 150, type: 'number' },
    { field: 'Account Balance', headerName: 'Account Balance', width: 150, type: 'number' },
    // Add more columns as needed
  ];

  return (
    <div style={{ height: 400, width: '100%' }}>
      <DataGrid
        rows={data}
        columns={columns}
        pageSize={5}
        rowsPerPageOptions={[5]}
        getRowId={(row) => row.Date + row.Description}  // Adjust this based on your data structure
      />
    </div>
  );
}

export default Spreadsheet;