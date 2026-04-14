import React, { useState } from 'react';
import { Box, Button, Container, TextField, Typography, Paper } from '@mui/material';
import { useTranslation } from 'react-i18next';

interface LoginProps {
  onLogin: (username: string) => void;
}

const Login: React.FC<LoginProps> = ({ onLogin }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { t } = useTranslation();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // 简单的模拟登录验证
    if (username && password) {
      // 实际项目中应该调用 API 进行验证
      onLogin(username);
    } else {
      setError('Please enter both username and password');
    }
  };

  return (
    <Container component="main" maxWidth="xs" sx={{ mt: 8 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Typography component="h1" variant="h5" align="center" sx={{ mb: 4 }}>
          {t('login.title')}
        </Typography>
        <Box component="form" onSubmit={handleSubmit} noValidate>
          {error && (
            <Typography color="error" variant="body2" sx={{ mb: 2 }}>
              {error}
            </Typography>
          )}
          <TextField
            variant="outlined"
            margin="normal"
            required
            fullWidth
            id="username"
            label={t('login.username')}
            name="username"
            autoComplete="username"
            autoFocus
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <TextField
            variant="outlined"
            margin="normal"
            required
            fullWidth
            name="password"
            label={t('login.password')}
            type="password"
            id="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <Button
            type="submit"
            fullWidth
            variant="contained"
            sx={{ mt: 3, mb: 2, bgcolor: '#1976d2' }}
          >
            {t('login.submit')}
          </Button>
        </Box>
      </Paper>
    </Container>
  );
};

export default Login;
