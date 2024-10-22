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
import FileUpload from './components/FileUpload';
import DarkModeToggle from './components/DarkModeToggle';
import Summary from './components/Summary';
import Spreadsheet from './components/Spreadsheet';
import FinancialOverview from './components/FinancialOverview';
import axios from 'axios';
import './styles/Dashboard.css';


const drawerWidth = 240;

function App() {
  const [darkMode, setDarkMode] = useState(false);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const theme = createTheme({
    palette: {
      mode: darkMode ? 'dark' : 'light',
    },
  });

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${process.env.REACT_APP_API_URL}/data`);
      setData(response.data);
    } catch (err) {
      setError('Failed to fetch data. Please try again.');
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleFileUpload = async (file, bank) => {
    setLoading(true);
    setError(null);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('bank', bank);

  //   try {
  //     await axios.post(`${process.env.REACT_APP_PDF_TO_CSV_URL}`, formData);
  //     await fetchData();
  //   } catch (err) {
  //     setError(`Failed to upload file for ${bank}. Please try again.`);
  //     console.error('Error uploading file:', err);
  //   } finally {
  //     setLoading(false);
  //   }
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
            <Box sx={{ flexGrow: 1 }} />
            {/* <DarkModeToggle darkMode={darkMode} setDarkMode={setDarkMode} /> */}
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
          {loading && <Typography>Loading...</Typography>}
          {error && <Typography color="error">{error}</Typography>}
          {data && !loading && !error && (
            <Container maxWidth="lg">
              <Box container spacing={3}>
                <Box sx={{ width: '100%' }}>
                  <Paper>
                    <Summary data={data} />
                  </Paper>
                </Box>
                <Box sx={{ width: '100%' }}>
                  <Paper>
                    <FinancialOverview data={data} />
                  </Paper>
                </Box>
                <Box sx={{ width: '100%' }}>
                  <Paper>
                    <Spreadsheet data={data} />
                  </Paper>
                </Box>
              </Box>
            </Container>
          )}
        </Box>
      </Box>
    </ThemeProvider>
  );
}

export default App;
