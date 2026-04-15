import React, { useState, useEffect, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Login from './components/Login';
import { PermissionProvider } from './contexts/PermissionContext';
import { AppBar, Box, CssBaseline, Drawer, IconButton, List, ListItem, ListItemButton, ListItemIcon, ListItemText, Toolbar, Typography, Button, FormControl, InputLabel, Select, MenuItem, useMediaQuery, useTheme } from '@mui/material';
import { Home, Task, Settings, ReceiptLong, Build, Logout, Menu, ChevronLeft } from '@mui/icons-material';
import log from './utils/logger';
import { startSpan, endSpan } from './utils/tracer';

// 懒加载组件
const Dashboard = React.lazy(() => import('./components/Dashboard'));
const TaskManagement = React.lazy(() => import('./components/TaskManagement'));
const Configuration = React.lazy(() => import('./components/Configuration'));
const AuditLogs = React.lazy(() => import('./components/AuditLogs'));
const ToolsList = React.lazy(() => import('./components/ToolsList'));

const App: React.FC = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState<string>('');
  const [userRole, setUserRole] = useState<string>('user'); // 默认角色
  const [drawerOpen, setDrawerOpen] = useState(true);
  const { t, i18n } = useTranslation();
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  
  // 移动设备默认关闭抽屉
  useEffect(() => {
    if (isMobile) {
      setDrawerOpen(false);
    }
  }, [isMobile]);
  
  // 监听路由变化，记录页面访问
  useEffect(() => {
    const span = startSpan('Page visit', {
      component: 'App',
      action: 'page_visit',
      userId: user || 'anonymous',
      page: location.pathname
    });
    
    log.infoWithMeta('Page visited', {
      component: 'App',
      action: 'page_visit',
      userId: user || 'anonymous',
      page: location.pathname
    });
    
    endSpan(span);
  }, [location.pathname, user]);
  
  const handleLanguageChange = (event: any) => {
    const newLanguage = event.target.value as string;
    const span = startSpan('Language change', {
      component: 'App',
      action: 'language_change',
      userId: user || 'anonymous',
      language: newLanguage
    });
    
    i18n.changeLanguage(newLanguage);
    
    log.infoWithMeta('Language changed', {
      component: 'App',
      action: 'language_change',
      userId: user || 'anonymous',
      language: newLanguage
    });
    
    endSpan(span);
  };

  const handleLogin = (username: string) => {
    const span = startSpan('User login', {
      component: 'App',
      action: 'login',
      userId: username
    });
    
    setUser(username);
    // 根据用户名设置角色（实际项目中应该从API获取）
    let role = 'user';
    if (username === 'admin') {
      role = 'admin';
    } else if (username === 'manager') {
      role = 'manager';
    }
    setUserRole(role);
    setIsLoggedIn(true);
    
    log.infoWithMeta('User logged in', {
      component: 'App',
      action: 'login',
      userId: username,
      role
    });
    
    span?.setAttribute('role', role);
    endSpan(span);
  };

  const handleLogout = () => {
    const currentUser = user;
    const span = startSpan('User logout', {
      component: 'App',
      action: 'logout',
      userId: currentUser
    });
    
    setIsLoggedIn(false);
    setUser('');
    setUserRole('user');
    
    log.infoWithMeta('User logged out', {
      component: 'App',
      action: 'logout',
      userId: currentUser
    });
    
    endSpan(span);
  };

  if (!isLoggedIn) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <PermissionProvider userRole={userRole}>
      <Router>
        <Box sx={{ display: 'flex' }}>
          <CssBaseline />
          <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
            <Toolbar>
              <IconButton
                color="inherit"
                aria-label="open drawer"
                edge="start"
                onClick={() => setDrawerOpen(!drawerOpen)}
                sx={{ mr: 2, display: { md: 'none' } }}
              >
                <Menu />
              </IconButton>
              <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                Ace Agent Control Panel
              </Typography>
              <FormControl sx={{ marginRight: 2, minWidth: 120, display: { xs: 'none', sm: 'block' } }}>
                <InputLabel id="language-select-label">{t('common.language')}</InputLabel>
                <Select
                  labelId="language-select-label"
                  value={i18n.language}
                  label={t('common.language')}
                  onChange={handleLanguageChange}
                >
                  <MenuItem value="en">English</MenuItem>
                  <MenuItem value="zh">中文</MenuItem>
                </Select>
              </FormControl>
              <Typography variant="body1" sx={{ marginRight: 2, display: { xs: 'none', sm: 'block' } }}>
                {t('common.welcome')}, {user} ({userRole})
              </Typography>
              <Button color="inherit" startIcon={<Logout />} onClick={handleLogout}>
                {t('common.logout')}
              </Button>
            </Toolbar>
          </AppBar>
          <Drawer
            variant={isMobile ? 'temporary' : 'permanent'}
            open={drawerOpen}
            onClose={() => setDrawerOpen(false)}
            sx={{
              width: 240,
              flexShrink: 0,
              [`& .MuiDrawer-paper`]: { 
                width: 240, 
                boxSizing: 'border-box',
                display: { xs: 'block', md: 'block' }
              },
            }}
          >
            <Toolbar>
              <IconButton onClick={() => setDrawerOpen(false)} sx={{ display: { md: 'none' } }}>
                <ChevronLeft />
              </IconButton>
            </Toolbar>
            <Box sx={{ overflow: 'auto' }}>
              <List>
                {/* 所有角色都可以访问的菜单项 */}
                <ListItem disablePadding>
                  <ListItemButton component={Link} to="/" onClick={() => isMobile && setDrawerOpen(false)}>
                    <ListItemIcon sx={{ color: '#1976d2' }}>
                      <Home />
                    </ListItemIcon>
                    <ListItemText primary={t('common.dashboard')} />
                  </ListItemButton>
                </ListItem>
                <ListItem disablePadding>
                  <ListItemButton component={Link} to="/tasks" onClick={() => isMobile && setDrawerOpen(false)}>
                    <ListItemIcon sx={{ color: '#1976d2' }}>
                      <Task />
                    </ListItemIcon>
                    <ListItemText primary={t('common.tasks')} />
                  </ListItemButton>
                </ListItem>
                <ListItem disablePadding>
                <ListItemButton component={Link} to="/tools" onClick={() => isMobile && setDrawerOpen(false)}>
                  <ListItemIcon sx={{ color: '#1976d2' }}>
                    <Build />
                  </ListItemIcon>
                  <ListItemText primary={t('common.tools')} />
                </ListItemButton>
              </ListItem>
                
                {/* 管理员和经理可以访问的菜单项 */}
                {(userRole === 'admin' || userRole === 'manager') && (
                  <ListItem disablePadding>
                    <ListItemButton component={Link} to="/configuration" onClick={() => isMobile && setDrawerOpen(false)}>
                      <ListItemIcon sx={{ color: '#1976d2' }}>
                        <Settings />
                      </ListItemIcon>
                      <ListItemText primary={t('common.configuration')} />
                    </ListItemButton>
                  </ListItem>
                )}
                
                {/* 只有管理员可以访问的菜单项 */}
              {userRole === 'admin' && (
                <ListItem disablePadding>
                  <ListItemButton component={Link} to="/audit" onClick={() => isMobile && setDrawerOpen(false)}>
                    <ListItemIcon sx={{ color: '#1976d2' }}>
                      <ReceiptLong />
                    </ListItemIcon>
                    <ListItemText primary={t('common.auditLogs')} />
                  </ListItemButton>
                </ListItem>
              )}
              </List>
            </Box>
          </Drawer>
          <Box component="main" sx={{ 
            flexGrow: 1, 
            p: { xs: 2, sm: 3 }, 
            mt: 8,
            ml: { xs: 0, md: 240 }
          }}>
            <Suspense fallback={<div>{t('common.loading')}</div>}>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/tasks" element={<TaskManagement />} />
                <Route path="/tools" element={<ToolsList />} />
                {(userRole === 'admin' || userRole === 'manager') && (
                  <Route path="/configuration" element={<Configuration />} />
                )}
                {userRole === 'admin' && (
                  <Route path="/audit" element={<AuditLogs />} />
                )}
              </Routes>
            </Suspense>
          </Box>
        </Box>
      </Router>
    </PermissionProvider>
  );
};

export default App;
