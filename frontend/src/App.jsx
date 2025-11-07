import React from 'react';
import { ThemeProvider, CssBaseline } from '@mui/material';
import theme from './theme/theme';
import VideoList from './components/VideoList';

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <VideoList />
    </ThemeProvider>
  );
}

export default App;





