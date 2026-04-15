import React, { useState, useEffect } from 'react';
import { Box, Grid, Paper, Typography, CircularProgress, Alert, Chip } from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts';
import log from '../utils/logger';
import { startSpan, endSpan } from '../utils/tracer';

const Dashboard: React.FC = () => {
  const [systemStatus, setSystemStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 模拟系统状态数据
  useEffect(() => {
    const fetchSystemStatus = async () => {
      const span = startSpan('Fetch system status', {
        component: 'Dashboard',
        action: 'fetch_system_status'
      });
      
      try {
        log.infoWithMeta('Fetching system status', {
          component: 'Dashboard',
          action: 'fetch_system_status'
        });
        
        // 实际项目中应该调用 API 获取系统状态
        await new Promise(resolve => setTimeout(resolve, 1000)); // 模拟网络延迟
        
        const statusData = {
          status: 'healthy',
          version: '2.0.0',
          components: {
            executor: {
              status: 'ready',
              tool_count: 15,
              cache_stats: {
                cache_hits: 120,
                cache_misses: 30,
                cache_hit_rate: 80
              }
            },
            workflow: {
              history_count: 50,
              memory_summary: {
                current_memory_usage_mb: 256,
                short_term_memory_count: 45,
                long_term_memory_keys: 20
              }
            }
          },
          server_time: new Date().toISOString(),
          metrics: {
            api_response_time: 120, // ms
            error_rate: 2.5, // %
            active_users: 15,
            request_count: 1200,
            cpu_usage: 45, // %
            memory_usage: 60, // %
            disk_usage: 35 // %
          },
          user_activity: [
            { name: '00:00', value: 5 },
            { name: '04:00', value: 2 },
            { name: '08:00', value: 15 },
            { name: '12:00', value: 25 },
            { name: '16:00', value: 30 },
            { name: '20:00', value: 20 }
          ],
          api_performance: [
            { name: 'GET /api/tasks', response_time: 80, error_rate: 1.2 },
            { name: 'POST /api/tasks', response_time: 150, error_rate: 2.8 },
            { name: 'GET /api/tools', response_time: 60, error_rate: 0.5 },
            { name: 'GET /api/config', response_time: 45, error_rate: 0.2 },
            { name: 'POST /api/auth', response_time: 100, error_rate: 3.5 }
          ]
        };
        
        setSystemStatus(statusData);
        
        log.infoWithMeta('System status fetched successfully', {
          component: 'Dashboard',
          action: 'fetch_system_status_success',
          status: statusData.status,
          active_users: statusData.metrics.active_users,
          error_rate: statusData.metrics.error_rate
        });
        
        // 添加追踪属性
        span?.setAttribute('status', statusData.status);
        span?.setAttribute('active_users', statusData.metrics.active_users.toString());
        span?.setAttribute('error_rate', statusData.metrics.error_rate.toString());
      } catch (err) {
        const errorMessage = 'Failed to fetch system status';
        setError(errorMessage);
        log.errorWithMeta(errorMessage, {
          component: 'Dashboard',
          action: 'fetch_system_status_error',
          error: err
        });
        
        // 记录错误信息到追踪
        span?.setAttribute('error', errorMessage);
        span?.setAttribute('error_details', err?.toString() || 'unknown error');
      } finally {
        setLoading(false);
        endSpan(span);
      }
    };

    fetchSystemStatus();
    
    // 定期刷新数据
    const interval = setInterval(fetchSystemStatus, 30000); // 每30秒刷新一次
    return () => clearInterval(interval);
  }, []);

  // 模拟任务统计数据
  const taskStats = [
    { name: 'Completed', value: 45 },
    { name: 'Pending', value: 15 },
    { name: 'Failed', value: 5 }
  ];

  const performanceData = [
    { name: 'Jan', value: 65 },
    { name: 'Feb', value: 59 },
    { name: 'Mar', value: 80 },
    { name: 'Apr', value: 81 },
    { name: 'May', value: 56 },
    { name: 'Jun', value: 55 }
  ];

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'green';
      case 'warning':
        return 'orange';
      case 'critical':
        return 'red';
      default:
        return 'gray';
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ mt: 4 }}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Dashboard
      </Typography>
      
      <Grid container spacing={3}>
        {/* System Status Card */}
        <Grid item xs={12} md={4}>
          <Paper elevation={3} sx={{ p: 3 }}>
            <Typography variant="h6" component="h2" gutterBottom>
              System Status
            </Typography>
            <Typography variant="body1">
              Status: <strong style={{ color: getStatusColor(systemStatus?.status || 'Unknown') }}>
                {systemStatus?.status || 'Unknown'}
              </strong>
            </Typography>
            <Typography variant="body1">
              Version: {systemStatus?.version || 'Unknown'}
            </Typography>
            <Typography variant="body1">
              Server Time: {new Date(systemStatus?.server_time || Date.now()).toLocaleString()}
            </Typography>
          </Paper>
        </Grid>

        {/* Task Statistics */}
        <Grid item xs={12} md={4}>
          <Paper elevation={3} sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" component="h2" gutterBottom>
              Task Statistics
            </Typography>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={taskStats}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }: any) => name ? `${name}: ${(percent * 100).toFixed(0)}%` : ''}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {taskStats.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* System Metrics */}
        <Grid item xs={12} md={4}>
          <Paper elevation={3} sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" component="h2" gutterBottom>
              System Metrics
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mt: 2 }}>
              <Chip 
                label={`API Response Time: ${systemStatus?.metrics?.api_response_time || 0}ms`} 
                color="primary" 
                variant="outlined" 
              />
              <Chip 
                label={`Error Rate: ${systemStatus?.metrics?.error_rate || 0}%`} 
                color={systemStatus?.metrics?.error_rate > 5 ? 'error' : 'success'} 
                variant="outlined" 
              />
              <Chip 
                label={`Active Users: ${systemStatus?.metrics?.active_users || 0}`} 
                color="info" 
                variant="outlined" 
              />
              <Chip 
                label={`Requests: ${systemStatus?.metrics?.request_count || 0}`} 
                color="secondary" 
                variant="outlined" 
              />
              <Chip 
                label={`CPU Usage: ${systemStatus?.metrics?.cpu_usage || 0}%`} 
                color={systemStatus?.metrics?.cpu_usage > 80 ? 'error' : 'success'} 
                variant="outlined" 
              />
              <Chip 
                label={`Memory Usage: ${systemStatus?.metrics?.memory_usage || 0}%`} 
                color={systemStatus?.metrics?.memory_usage > 80 ? 'error' : 'success'} 
                variant="outlined" 
              />
              <Chip 
                label={`Disk Usage: ${systemStatus?.metrics?.disk_usage || 0}%`} 
                color={systemStatus?.metrics?.disk_usage > 80 ? 'error' : 'success'} 
                variant="outlined" 
              />
            </Box>
          </Paper>
        </Grid>

        {/* Executor Status */}
        <Grid item xs={12} md={6}>
          <Paper elevation={3} sx={{ p: 3 }}>
            <Typography variant="h6" component="h2" gutterBottom>
              Executor Status
            </Typography>
            <Typography variant="body1">
              Status: <strong>{systemStatus?.components?.executor?.status || 'Unknown'}</strong>
            </Typography>
            <Typography variant="body1">
              Tool Count: {systemStatus?.components?.executor?.tool_count || 0}
            </Typography>
            <Typography variant="body1">
              Cache Hit Rate: {systemStatus?.components?.executor?.cache_stats?.cache_hit_rate || 0}%
            </Typography>
            <Typography variant="body1">
              Cache Hits: {systemStatus?.components?.executor?.cache_stats?.cache_hits || 0}
            </Typography>
            <Typography variant="body1">
              Cache Misses: {systemStatus?.components?.executor?.cache_stats?.cache_misses || 0}
            </Typography>
          </Paper>
        </Grid>

        {/* Workflow Status */}
        <Grid item xs={12} md={6}>
          <Paper elevation={3} sx={{ p: 3 }}>
            <Typography variant="h6" component="h2" gutterBottom>
              Workflow Status
            </Typography>
            <Typography variant="body1">
              History Count: {systemStatus?.components?.workflow?.history_count || 0}
            </Typography>
            <Typography variant="body1">
              Memory Usage: {systemStatus?.components?.workflow?.memory_summary?.current_memory_usage_mb || 0} MB
            </Typography>
            <Typography variant="body1">
              Short-term Memory: {systemStatus?.components?.workflow?.memory_summary?.short_term_memory_count || 0} items
            </Typography>
            <Typography variant="body1">
              Long-term Memory: {systemStatus?.components?.workflow?.memory_summary?.long_term_memory_keys || 0} keys
            </Typography>
          </Paper>
        </Grid>

        {/* User Activity */}
        <Grid item xs={12} md={6}>
          <Paper elevation={3} sx={{ p: 3 }}>
            <Typography variant="h6" component="h2" gutterBottom>
              User Activity
            </Typography>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={systemStatus?.user_activity || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="value" stroke="#1976d2" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* API Performance */}
        <Grid item xs={12} md={6}>
          <Paper elevation={3} sx={{ p: 3 }}>
            <Typography variant="h6" component="h2" gutterBottom>
              API Performance
            </Typography>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={systemStatus?.api_performance || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="response_time" name="Response Time (ms)" fill="#1976d2" />
                <Bar dataKey="error_rate" name="Error Rate (%)" fill="#ff8042" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
