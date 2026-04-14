import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Dashboard from './components/Dashboard';
import TaskManagement from './components/TaskManagement';
import Configuration from './components/Configuration';
import AuditLogs from './components/AuditLogs';
import ToolsList from './components/ToolsList';
import Login from './components/Login';
import { AppBar, Box, CssBaseline, Drawer, IconButton, List, ListItem, ListItemButton, ListItemIcon, ListItemText, Toolbar, Typography, Button, FormControl, InputLabel, Select, MenuItem } from '@mui/material';
import { Home, Task, Settings, Logs, Wrench, Logout } from '@mui/icons-material';

const App: React.FC = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState<string>('');
  const { t, i18n } = useTranslation();
  
  const handleLanguageChange = (event: React.ChangeEvent<{ value: unknown }>) => {
    const newLanguage = event.target.value as string;
    i18n.changeLanguage(newLanguage);
  };

  const handleLogin = (username: string) => {
    setUser(username);
    setIsLoggedIn(true);
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setUser('');
  };

  if (!isLoggedIn) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <Router>
      <Box sx={{ display: 'flex' }}>
        <CssBaseline />
        <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              Ace Agent Control Panel
            </Typography>
            <FormControl sx={{ marginRight: 2, minWidth: 120 }}>
              <InputLabel id="language-select-label">Language</InputLabel>
              <Select
                labelId="language-select-label"
                value={i18n.language}
                label="Language"
                onChange={handleLanguageChange}
              >
                <MenuItem value="en">English</MenuItem>
                <MenuItem value="zh">中文</MenuItem>
              </Select>
            </FormControl>
            <Typography variant="body1" sx={{ marginRight: 2 }}>
              Welcome, {user}
            </Typography>
            <Button color="inherit" startIcon={<Logout />} onClick={handleLogout}>
              {t('common.logout')}
            </Button>
          </Toolbar>
        </AppBar>
        <Drawer
          variant="permanent"
          sx={{
            width: 240,
            flexShrink: 0,
            [`& .MuiDrawer-paper`]: { width: 240, boxSizing: 'border-box' },
          }}
        >
          <Toolbar />
          <Box sx={{ overflow: 'auto' }}>
            <List>
              <ListItem disablePadding>
                <ListItemButton component={Link} to="/">
                  <ListItemIcon sx={{ color: '#1976d2' }}>
                    <Home />
                  </ListItemIcon>
                  <ListItemText primary={t('common.dashboard')} />
                </ListItemButton>
              </ListItem>
              <ListItem disablePadding>
                <ListItemButton component={Link} to="/tasks">
                  <ListItemIcon sx={{ color: '#1976d2' }}>
                    <Task />
                  </ListItemIcon>
                  <ListItemText primary={t('common.tasks')} />
                </ListItemButton>
              </ListItem>
              <ListItem disablePadding>
                <ListItemButton component={Link} to="/tools">
                  <ListItemIcon sx={{ color: '#1976d2' }}>
                    <Wrench />
                  </ListItemIcon>
                  <ListItemText primary={t('common.tools')} />
                </ListItemButton>
              </ListItem>
              <ListItem disablePadding>
                <ListItemButton component={Link} to="/configuration">
                  <ListItemIcon sx={{ color: '#1976d2' }}>
                    <Settings />
                  </ListItemIcon>
                  <ListItemText primary={t('common.configuration')} />
                </ListItemButton>
              </ListItem>
              <ListItem disablePadding>
                <ListItemButton component={Link} to="/audit">
                  <ListItemIcon sx={{ color: '#1976d2' }}>
                    <Logs />
                  </ListItemIcon>
                  <ListItemText primary={t('common.auditLogs')} />
                </ListItemButton>
              </ListItem>
            </List>
          </Box>
        </Drawer>
        <Box component="main" sx={{ flexGrow: 1, p: 3, mt: 8 }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/tasks" element={<TaskManagement />} />
            <Route path="/tools" element={<ToolsList />} />
            <Route path="/configuration" element={<Configuration />} />
            <Route path="/audit" element={<AuditLogs />} />
          </Routes>
        </Box>
      </Box>
    </Router>
  );
};

export default App;
