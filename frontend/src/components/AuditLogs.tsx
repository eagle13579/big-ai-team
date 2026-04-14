import React, { useState, useEffect } from 'react';
import { Box, Paper, Typography, List, ListItem, ListItemText, CircularProgress, Alert, TextField, Button, InputAdornment } from '@mui/material';
import { Search, FilterList } from '@mui/icons-material';

interface AuditLog {
  id: string;
  timestamp: string;
  user: string;
  resource: string;
  action: string;
  status: string;
  details?: string;
}

const AuditLogs: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [filteredLogs, setFilteredLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('');

  // 模拟审计日志数据
  useEffect(() => {
    fetchLogs();
  }, []);

  useEffect(() => {
    filterLogs();
  }, [logs, searchTerm, filterStatus]);

  const fetchLogs = async () => {
    try {
      // 实际项目中应该调用 API 获取审计日志
      await new Promise(resolve => setTimeout(resolve, 1000)); // 模拟网络延迟
      
      setLogs([
        {
          id: '1',
          timestamp: new Date(Date.now() - 3600000).toISOString(),
          user: 'admin',
          resource: 'tasks',
          action: 'create',
          status: 'success',
          details: 'Created task: 帮我调研 Ace 浏览器的 2026 年市场表现并生成一份 Markdown 报告'
        },
        {
          id: '2',
          timestamp: new Date(Date.now() - 3500000).toISOString(),
          user: 'user1',
          resource: 'tools',
          action: 'list',
          status: 'success'
        },
        {
          id: '3',
          timestamp: new Date(Date.now() - 3400000).toISOString(),
          user: 'user2',
          resource: 'auth',
          action: 'login',
          status: 'failure',
          details: 'Invalid username or password'
        },
        {
          id: '4',
          timestamp: new Date(Date.now() - 3300000).toISOString(),
          user: 'admin',
          resource: 'config',
          action: 'read',
          status: 'success'
        },
        {
          id: '5',
          timestamp: new Date(Date.now() - 3200000).toISOString(),
          user: 'user1',
          resource: 'tasks',
          action: 'create',
          status: 'success',
          details: 'Created task: 计算 100 到 200 之间的质数和'
        },
        {
          id: '6',
          timestamp: new Date(Date.now() - 3100000).toISOString(),
          user: 'user3',
          resource: 'auth',
          action: 'login',
          status: 'success'
        },
        {
          id: '7',
          timestamp: new Date(Date.now() - 3000000).toISOString(),
          user: 'admin',
          resource: 'audit/logs',
          action: 'read',
          status: 'success'
        }
      ]);
    } catch (err) {
      setError('Failed to fetch audit logs');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const filterLogs = () => {
    let filtered = [...logs];

    if (searchTerm) {
      filtered = filtered.filter(log => 
        log.user.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.resource.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (log.details && log.details.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }

    if (filterStatus) {
      filtered = filtered.filter(log => log.status === filterStatus);
    }

    setFilteredLogs(filtered);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'green';
      case 'failure':
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
        Audit Logs
      </Typography>

      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
          <TextField
            fullWidth
            variant="outlined"
            placeholder="Search logs..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Search />
                </InputAdornment>
              ),
            }}
          />
          <TextField
            select
            variant="outlined"
            label="Status"
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            sx={{ minWidth: 150 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <FilterList />
                </InputAdornment>
              ),
            }}
          >
            <option value="">All</option>
            <option value="success">Success</option>
            <option value="failure">Failure</option>
          </TextField>
        </Box>
      </Paper>

      <Paper elevation={3} sx={{ p: 3 }}>
        <Typography variant="h6" component="h2" gutterBottom>
          Log Entries
        </Typography>
        {filteredLogs.length === 0 ? (
          <Typography variant="body1" color="textSecondary" align="center" sx={{ py: 2 }}>
            No logs found matching your filters.
          </Typography>
        ) : (
          <List>
            {filteredLogs.map((log) => (
              <ListItem key={log.id} sx={{ mb: 1, borderRadius: 1, bgcolor: '#f5f5f5' }}>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span>{log.user} - {log.action} {log.resource}</span>
                      <span style={{ color: getStatusColor(log.status), fontWeight: 'bold' }}>
                        {log.status}
                      </span>
                    </Box>
                  }
                  secondary={
                    <Box>
                      <Typography variant="body2">
                        {new Date(log.timestamp).toLocaleString()}
                      </Typography>
                      {log.details && (
                        <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                          {log.details}
                        </Typography>
                      )}
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        )}
      </Paper>
    </Box>
  );
};

export default AuditLogs;
