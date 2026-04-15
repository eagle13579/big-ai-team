import React, { createContext, useContext, ReactNode } from 'react';

interface PermissionContextType {
  userRole: string;
  hasPermission: (resource: string, action: string) => boolean;
}

const PermissionContext = createContext<PermissionContextType | undefined>(undefined);

export const usePermission = () => {
  const context = useContext(PermissionContext);
  if (!context) {
    throw new Error('usePermission must be used within a PermissionProvider');
  }
  return context;
};

interface PermissionProviderProps {
  children: ReactNode;
  userRole: string;
}

// 定义权限矩阵
const permissions = {
  admin: {
    users: ['create', 'read', 'update', 'delete'],
    tasks: ['create', 'read', 'update', 'delete', 'execute'],
    tools: ['create', 'read', 'update', 'delete'],
    configuration: ['read', 'update'],
    audit: ['read', 'export']
  },
  manager: {
    users: ['read', 'update'],
    tasks: ['create', 'read', 'update', 'execute'],
    tools: ['read', 'update'],
    configuration: ['read'],
    audit: ['read']
  },
  user: {
    tasks: ['create', 'read', 'execute'],
    tools: ['read']
  },
  guest: {
    tasks: ['read'],
    tools: ['read']
  }
};

export const PermissionProvider: React.FC<PermissionProviderProps> = ({ children, userRole }) => {
  const hasPermission = (resource: string, action: string): boolean => {
    const rolePermissions = permissions[userRole as keyof typeof permissions] || permissions.guest;
    return rolePermissions[resource as keyof typeof rolePermissions]?.includes(action) || false;
  };

  return (
    <PermissionContext.Provider value={{ userRole, hasPermission }}>
      {children}
    </PermissionContext.Provider>
  );
};
