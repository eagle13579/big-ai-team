import React, { useState, useEffect } from 'react';
import { Box, Paper, Typography, TextField, Button, CircularProgress, Alert, FormControlLabel, Switch } from '@mui/material';

interface Config {
  projectName: string;
  envMode: string;
  configVersion: string;
  accessTokenExpireMinutes: number;
  agentMaxSteps: number;
  cacheTtl: number;
  maxConcurrentTasks: number;
  agentOutputDir: string;
  defaultModelName: string;
}

const Configuration: React.FC = () => {
  const [config, setConfig] = useState<Config | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // 模拟配置数据
  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      // 实际项目中应该调用 API 获取配置
      await new Promise(resolve => setTimeout(resolve, 1000)); // 模拟网络延迟
      
      setConfig({
        projectName: 'Ace Agent',
        envMode: 'development',
        configVersion: '2.0.0',
        accessTokenExpireMinutes: 30,
        agentMaxSteps: 10,
        cacheTtl: 3600,
        maxConcurrentTasks: 10,
        agentOutputDir: 'output',
        defaultModelName: 'gpt-4'
      });
    } catch (err) {
      setError('Failed to fetch configuration');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveConfig = async () => {
    if (!config) return;

    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      // 实际项目中应该调用 API 保存配置
      await new Promise(resolve => setTimeout(resolve, 1500)); // 模拟网络延迟
      
      setSuccess('Configuration saved successfully');
      // 3秒后清除成功消息
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError('Failed to save configuration');
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const handleConfigChange = (field: keyof Config, value: any) => {
    if (config) {
      setConfig(prev => prev ? { ...prev, [field]: value } : null);
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

  if (!config) {
    return (
      <Box sx={{ mt: 4 }}>
        <Alert severity="error">No configuration data available</Alert>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Configuration
      </Typography>

      <Paper elevation={3} sx={{ p: 3 }}>
        <Typography variant="h6" component="h2" gutterBottom>
          System Settings
        </Typography>
        
        {success && (
          <Alert severity="success" sx={{ mb: 2 }}>
            {success}
          </Alert>
        )}

        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3, mb: 3 }}>
          <TextField
            label="Project Name"
            variant="outlined"
            fullWidth
            value={config.projectName}
            onChange={(e) => handleConfigChange('projectName', e.target.value)}
          />
          <TextField
            label="Environment Mode"
            variant="outlined"
            fullWidth
            value={config.envMode}
            onChange={(e) => handleConfigChange('envMode', e.target.value)}
          />
          <TextField
            label="Config Version"
            variant="outlined"
            fullWidth
            value={config.configVersion}
            onChange={(e) => handleConfigChange('configVersion', e.target.value)}
          />
          <TextField
            label="Default Model Name"
            variant="outlined"
            fullWidth
            value={config.defaultModelName}
            onChange={(e) => handleConfigChange('defaultModelName', e.target.value)}
          />
          <TextField
            label="Access Token Expire (minutes)"
            variant="outlined"
            fullWidth
            type="number"
            value={config.accessTokenExpireMinutes}
            onChange={(e) => handleConfigChange('accessTokenExpireMinutes', parseInt(e.target.value) || 0)}
          />
          <TextField
            label="Agent Max Steps"
            variant="outlined"
            fullWidth
            type="number"
            value={config.agentMaxSteps}
            onChange={(e) => handleConfigChange('agentMaxSteps', parseInt(e.target.value) || 0)}
          />
          <TextField
            label="Cache TTL (seconds)"
            variant="outlined"
            fullWidth
            type="number"
            value={config.cacheTtl}
            onChange={(e) => handleConfigChange('cacheTtl', parseInt(e.target.value) || 0)}
          />
          <TextField
            label="Max Concurrent Tasks"
            variant="outlined"
            fullWidth
            type="number"
            value={config.maxConcurrentTasks}
            onChange={(e) => handleConfigChange('maxConcurrentTasks', parseInt(e.target.value) || 0)}
          />
          <TextField
            label="Agent Output Directory"
            variant="outlined"
            fullWidth
            value={config.agentOutputDir}
            onChange={(e) => handleConfigChange('agentOutputDir', e.target.value)}
          />
        </Box>

        <Button
          variant="contained"
          onClick={handleSaveConfig}
          disabled={saving}
          sx={{ bgcolor: '#1976d2' }}
        >
          {saving ? <CircularProgress size={20} color="inherit" /> : 'Save Configuration'}
        </Button>
      </Paper>
    </Box>
  );
};

export default Configuration;
