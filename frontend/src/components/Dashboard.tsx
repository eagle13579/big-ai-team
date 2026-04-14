import React, { useState, useEffect } from 'react';
import { Box, Grid, Paper, Typography, CircularProgress, Alert } from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const Dashboard: React.FC = () => {
  const [systemStatus, setSystemStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 模拟系统状态数据
  useEffect(() => {
    const fetchSystemStatus = async () => {
      try {
        // 实际项目中应该调用 API 获取系统状态
        await new Promise(resolve => setTimeout(resolve, 1000)); // 模拟网络延迟
        
        setSystemStatus({
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
          server_time: new Date().toISOString()
        });
      } catch (err) {
        setError('Failed to fetch system status');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchSystemStatus();
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
              Status: <strong>{systemStatus?.status || 'Unknown'}</strong>
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
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
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

        {/* Performance Metrics */}
        <Grid item xs={12} md={4}>
          <Paper elevation={3} sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" component="h2" gutterBottom>
              Performance Metrics
            </Typography>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#1976d2" />
              </BarChart>
            </ResponsiveContainer>
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
      </Grid>
    </Box>
  );
};

export default Dashboard;
