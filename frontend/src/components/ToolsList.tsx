import React, { useState, useEffect } from 'react';
import { Box, Paper, Typography, List, ListItem, ListItemText, ListItemIcon, CircularProgress, Alert } from '@mui/material';
import { Build, Search, Create, Description, Folder, Delete, Info } from '@mui/icons-material';

interface Tool {
  name: string;
  description: string;
  category: string;
  status: 'active' | 'inactive' | 'degraded';
}

const ToolsList: React.FC = () => {
  const [tools, setTools] = useState<Tool[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 模拟工具数据
  useEffect(() => {
    fetchTools();
  }, []);

  const fetchTools = async () => {
    try {
      // 实际项目中应该调用 API 获取工具列表
      await new Promise(resolve => setTimeout(resolve, 1000)); // 模拟网络延迟
      
      setTools([
        {
          name: 'web_search',
          description: 'Search the web for information',
          category: 'Web',
          status: 'active'
        },
        {
          name: 'write_file',
          description: 'Write content to a file',
          category: 'File',
          status: 'active'
        },
        {
          name: 'read_file',
          description: 'Read content from a file',
          category: 'File',
          status: 'active'
        },
        {
          name: 'list_files',
          description: 'List files in the workspace',
          category: 'File',
          status: 'active'
        },
        {
          name: 'delete_file',
          description: 'Delete a file from the workspace',
          category: 'File',
          status: 'active'
        },
        {
          name: 'get_system_status',
          description: 'Get current system status',
          category: 'System',
          status: 'active'
        },
        {
          name: 'calculator',
          description: 'Perform mathematical calculations',
          category: 'Utility',
          status: 'active'
        },
        {
          name: 'code_interpreter',
          description: 'Interpret and execute code',
          category: 'Development',
          status: 'active'
        },
        {
          name: 'data_analyzer',
          description: 'Analyze data and generate insights',
          category: 'Data',
          status: 'active'
        },
        {
          name: 'file_manager',
          description: 'Manage files and directories',
          category: 'File',
          status: 'active'
        },
        {
          name: 'file_ops',
          description: 'Perform file operations',
          category: 'File',
          status: 'active'
        },
        {
          name: 'git_helper',
          description: 'Perform Git operations',
          category: 'Development',
          status: 'active'
        },
        {
          name: 'agent_reach',
          description: 'Communicate with other agents',
          category: 'Agent',
          status: 'active'
        }
      ]);
    } catch (err) {
      setError('Failed to fetch tools');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getToolIcon = (toolName: string) => {
    switch (toolName) {
      case 'web_search':
        return <Search color="primary" />;
      case 'write_file':
        return <Create color="primary" />;
      case 'read_file':
        return <Description color="primary" />;
      case 'list_files':
        return <Folder color="primary" />;
      case 'delete_file':
        return <Delete color="primary" />;
      default:
        return <Build color="primary" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'green';
      case 'inactive':
        return 'red';
      case 'degraded':
        return 'orange';
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
        Available Tools
      </Typography>
      
      <Paper elevation={3} sx={{ p: 3 }}>
        <Typography variant="h6" component="h2" gutterBottom>
          Tool Registry
        </Typography>
        {tools.length === 0 ? (
          <Typography variant="body1" color="textSecondary" align="center" sx={{ py: 2 }}>
            No tools found.
          </Typography>
        ) : (
          <List>
            {tools.map((tool) => (
              <ListItem key={tool.name} sx={{ mb: 1, borderRadius: 1, bgcolor: '#f5f5f5' }}>
                <ListItemIcon>
                  {getToolIcon(tool.name)}
                </ListItemIcon>
                <ListItemText
                  primary={tool.name}
                  secondary={
                    <Box>
                      <Typography variant="body2">
                        {tool.description}
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 2, mt: 1 }}>
                        <Typography variant="body2" sx={{ color: 'textSecondary' }}>
                          Category: {tool.category}
                        </Typography>
                        <Typography 
                          variant="body2" 
                          sx={{ color: getStatusColor(tool.status), fontWeight: 'bold' }}
                        >
                          Status: {tool.status}
                        </Typography>
                      </Box>
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

export default ToolsList;
