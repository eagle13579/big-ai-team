import React, { useState, useEffect } from 'react';
import { Box, Button, Paper, Typography, TextField, List, ListItem, ListItemText, ListItemSecondaryAction, IconButton, CircularProgress, Alert, Select, MenuItem, FormControl, InputLabel } from '@mui/material';
import { PlayArrow, Stop, Delete, Refresh } from '@mui/icons-material';

interface Task {
  id: string;
  query: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'timeout';
  startTime: string;
  endTime?: string;
  steps?: any[];
  finalAnswer?: string;
}

const TaskManagement: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [newTaskQuery, setNewTaskQuery] = useState('');
  const [maxSteps, setMaxSteps] = useState(10);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  // 模拟任务数据
  useEffect(() => {
    fetchTasks();
  }, []);

  const fetchTasks = async () => {
    setRefreshing(true);
    try {
      // 实际项目中应该调用 API 获取任务列表
      await new Promise(resolve => setTimeout(resolve, 500)); // 模拟网络延迟
      
      setTasks([
        {
          id: '1',
          query: '帮我调研 Ace 浏览器的 2026 年市场表现并生成一份 Markdown 报告',
          status: 'completed',
          startTime: new Date(Date.now() - 3600000).toISOString(),
          endTime: new Date(Date.now() - 3500000).toISOString(),
          finalAnswer: '调研报告已生成并保存至 research_report.md'
        },
        {
          id: '2',
          query: '计算 100 到 200 之间的质数和',
          status: 'completed',
          startTime: new Date(Date.now() - 7200000).toISOString(),
          endTime: new Date(Date.now() - 7190000).toISOString(),
          finalAnswer: '100 到 200 之间的质数和为 3167'
        },
        {
          id: '3',
          query: '搜索最新的 AI 技术趋势',
          status: 'pending',
          startTime: new Date().toISOString()
        }
      ]);
    } catch (err) {
      setError('Failed to fetch tasks');
      console.error(err);
    } finally {
      setRefreshing(false);
    }
  };

  const handleCreateTask = async () => {
    if (!newTaskQuery.trim()) {
      setError('Please enter a task query');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // 实际项目中应该调用 API 创建任务
      await new Promise(resolve => setTimeout(resolve, 1000)); // 模拟网络延迟

      const newTask: Task = {
        id: Date.now().toString(),
        query: newTaskQuery,
        status: 'pending',
        startTime: new Date().toISOString()
      };

      setTasks(prevTasks => [newTask, ...prevTasks]);
      setNewTaskQuery('');
    } catch (err) {
      setError('Failed to create task');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleExecuteTask = async (taskId: string) => {
    setLoading(true);
    try {
      // 实际项目中应该调用 API 执行任务
      await new Promise(resolve => setTimeout(resolve, 1500)); // 模拟网络延迟

      setTasks(prevTasks => prevTasks.map(task => 
        task.id === taskId 
          ? { ...task, status: 'running' }
          : task
      ));

      // 模拟任务完成
      setTimeout(() => {
        setTasks(prevTasks => prevTasks.map(task => 
          task.id === taskId 
            ? { 
                ...task, 
                status: 'completed', 
                endTime: new Date().toISOString(),
                finalAnswer: 'Task completed successfully'
              }
            : task
        ));
        setLoading(false);
      }, 3000);
    } catch (err) {
      setError('Failed to execute task');
      console.error(err);
      setLoading(false);
    }
  };

  const handleDeleteTask = async (taskId: string) => {
    try {
      // 实际项目中应该调用 API 删除任务
      await new Promise(resolve => setTimeout(resolve, 500)); // 模拟网络延迟

      setTasks(prevTasks => prevTasks.filter(task => task.id !== taskId));
    } catch (err) {
      setError('Failed to delete task');
      console.error(err);
    }
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Task Management
      </Typography>

      {/* Create Task Form */}
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" component="h2" gutterBottom>
          Create New Task
        </Typography>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        <TextField
          fullWidth
          multiline
          rows={3}
          label="Task Query"
          variant="outlined"
          value={newTaskQuery}
          onChange={(e) => setNewTaskQuery(e.target.value)}
          sx={{ mb: 2 }}
        />
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'end' }}>
          <FormControl fullWidth sx={{ maxWidth: 200 }}>
            <InputLabel>Max Steps</InputLabel>
            <Select
              label="Max Steps"
              value={maxSteps}
              onChange={(e) => setMaxSteps(e.target.value as number)}
            >
              <MenuItem value={5}>5</MenuItem>
              <MenuItem value={10}>10</MenuItem>
              <MenuItem value={15}>15</MenuItem>
              <MenuItem value={20}>20</MenuItem>
            </Select>
          </FormControl>
          <Button
            variant="contained"
            onClick={handleCreateTask}
            disabled={loading}
            sx={{ bgcolor: '#1976d2' }}
          >
            {loading ? <CircularProgress size={20} color="inherit" /> : 'Create Task'}
          </Button>
        </Box>
      </Paper>

      {/* Task List */}
      <Paper elevation={3} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" component="h2">
            Task List
          </Typography>
          <IconButton onClick={fetchTasks} disabled={refreshing}>
            <Refresh />
          </IconButton>
        </Box>
        {tasks.length === 0 ? (
          <Typography variant="body1" color="textSecondary" align="center" sx={{ py: 2 }}>
            No tasks found. Create a new task above.
          </Typography>
        ) : (
          <List>
            {tasks.map((task) => (
              <ListItem key={task.id} sx={{ mb: 1, borderRadius: 1, bgcolor: '#f5f5f5' }}>
                <ListItemText
                  primary={task.query}
                  secondary={
                    <Box>
                      <Typography variant="body2">
                        Status: <strong>{task.status}</strong>
                      </Typography>
                      <Typography variant="body2">
                        Started: {new Date(task.startTime).toLocaleString()}
                      </Typography>
                      {task.endTime && (
                        <Typography variant="body2">
                          Ended: {new Date(task.endTime).toLocaleString()}
                        </Typography>
                      )}
                      {task.finalAnswer && (
                        <Typography variant="body2" color="primary">
                          Result: {task.finalAnswer}
                        </Typography>
                      )}
                    </Box>
                  }
                />
                <ListItemSecondaryAction>
                  {task.status === 'pending' && (
                    <IconButton edge="end" aria-label="execute" onClick={() => handleExecuteTask(task.id)}>
                      <PlayArrow />
                    </IconButton>
                  )}
                  <IconButton edge="end" aria-label="delete" onClick={() => handleDeleteTask(task.id)}>
                    <Delete />
                  </IconButton>
                </ListItemSecondaryAction>
              </ListItem>
            ))}
          </List>
        )}
      </Paper>
    </Box>
  );
};

export default TaskManagement;
