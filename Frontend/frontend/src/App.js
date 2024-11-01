import React, { useState, useEffect } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Box from '@mui/material/Box';
import Drawer from '@mui/material/Drawer';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Container from '@mui/material/Container';
import Paper from '@mui/material/Paper';
import Modal from '@mui/material/Modal';
import CircularProgress from '@mui/material/CircularProgress';
import FileUpload from './components/FileUpload';
import Summary from './components/Summary';
import Spreadsheet from './components/Spreadsheet';
import FinancialOverview from './components/FinancialOverview';
import axios from 'axios';
import './styles/Dashboard.css';

const drawerWidth = 240;
const API_URL = '/api/convert';  // This will be proxied to the backend

function App() {
  const [darkMode, setDarkMode] = useState(false);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dashboardData, setDashboardData] = useState(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const theme = createTheme({
    palette: {
      mode: darkMode ? 'dark' : 'light',
    },
  });

  const fetchDashboardData = async () => {
    try {
      const response = await axios.get('/api/data');
      setDashboardData(response.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setError('Failed to fetch dashboard data. Please try again.');
    }
  };

  useEffect(() => {
    console.log("API URL:", process.env.REACT_APP_PDF_TO_CSV_URL);
  }, []);

  const handleFileUpload = async (file, bank) => {
    setLoading(true);
    setError(null);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('bank', bank);

    try {
      console.log("Uploading to:", API_URL);
      const response = await axios.post(API_URL, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setData(response.data);
      // Handle successful upload (e.g., show a success message)
      console.log('Upload successful:', response.data);
      if (response.data) {
        await fetchDashboardData();
      }
    } catch (err) {
      setError(`Failed to upload file for ${bank}. Please try again.`);
      console.error('Error uploading file:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <Box sx={{ display: 'flex' }}>
        <CssBaseline />
        <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
          <Toolbar>
            <Typography variant="h6" noWrap component="div">
              Expense Management Dashboard
            </Typography>
          </Toolbar>
        </AppBar>
        <Drawer
          variant="permanent"
          sx={{
            width: drawerWidth,
            flexShrink: 0,
            [`& .MuiDrawer-paper`]: { width: drawerWidth, boxSizing: 'border-box' },
          }}
        >
          <Toolbar />
          <Box sx={{ overflow: 'auto' }}>
            <FileUpload onFileUpload={handleFileUpload} />
          </Box>
        </Drawer>
        <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
          <Toolbar />
          {error && <Typography color="error">{error}</Typography>}
          {dashboardData && !loading && !error && (
            <Container maxWidth="lg">
              <Box container spacing={3}>
                <Box sx={{ width: '100%' }}>
                  <Paper>
                    {/* <Summary data={dashboardData} /> */}
                  </Paper>
                </Box>
                <Box sx={{ width: '100%' }}>
                  <Paper>
                    {/* <FinancialOverview data={dashboardData} /> */}
                  </Paper>
                </Box>
                <Box sx={{ width: '100%' }}>
                  <Paper>
                    <Spreadsheet data={dashboardData} />
                  </Paper>
                </Box>
              </Box>
            </Container>
          )}
        </Box>
        <Modal
          open={loading}
          aria-labelledby="loading-modal-title"
          aria-describedby="loading-modal-description"
        >
          <Box sx={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: 400,
            bgcolor: 'background.paper',
            border: '2px solid #000',
            boxShadow: 24,
            p: 4,
            textAlign: 'center',
          }}>
            <Typography id="loading-modal-title" variant="h6" component="h2">
              Uploading File
            </Typography>
            <CircularProgress sx={{ mt: 2 }} />
          </Box>
        </Modal>
      </Box>
    </ThemeProvider>
  );
}

export default App;
