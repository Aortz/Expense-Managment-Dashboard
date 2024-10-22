import React, { useState } from 'react';
import { Button, Typography, Select, MenuItem, FormControl, InputLabel, Box } from '@mui/material';
import { CloudUpload } from '@mui/icons-material';

const banks = ['Citi', 'UOB', 'DBS'];

function FileUpload({ onFileUpload }) {
  const [selectedBank, setSelectedBank] = useState('');
  const [selectedFiles, setSelectedFiles] = useState([]);

  const handleBankChange = (event) => {
    setSelectedBank(event.target.value);
  };

  const handleFileChange = (event) => {
    setSelectedFiles(Array.from(event.target.files));
  };

  const handleUpload = () => {
    if (selectedBank && selectedFiles.length > 0) {
      selectedFiles.forEach(file => {
        onFileUpload(file, selectedBank);
      });
      // Reset selection after upload
      setSelectedFiles([]);
      setSelectedBank('');
    } else {
      alert('Please select a bank and at least one file.');
    }
  };

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>Upload PDF Statements</Typography>
      <FormControl fullWidth margin="normal">
        <InputLabel id="bank-select-label">Select Bank</InputLabel>
        <Select
          labelId="bank-select-label"
          value={selectedBank}
          onChange={handleBankChange}
          label="Select Bank"
        >
          {banks.map((bank) => (
            <MenuItem key={bank} value={bank}>{bank}</MenuItem>
          ))}
        </Select>
      </FormControl>
      <input
        accept=".pdf"
        style={{ display: 'none' }}
        id="raised-button-file"
        multiple
        type="file"
        onChange={handleFileChange}
      />
      <label htmlFor="raised-button-file">
        <Button variant="outlined" component="span" startIcon={<CloudUpload />} fullWidth sx={{ mt: 2 }}>
          Select Files
        </Button>
      </label>
      {selectedFiles.length > 0 && (
        <Typography variant="body2" sx={{ mt: 1 }}>
          {selectedFiles.length} file(s) selected
        </Typography>
      )}
      <Button 
        variant="contained" 
        onClick={handleUpload} 
        disabled={!selectedBank || selectedFiles.length === 0}
        fullWidth 
        sx={{ mt: 2 }}
      >
        Upload
      </Button>
    </Box>
  );
}

export default FileUpload;