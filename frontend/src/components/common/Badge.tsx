/**
 * Badge Component
 * Status badges with different variants and sizes
 */

import React from 'react';
import './Badge.css';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'danger' | 'info';
  size?: 'small' | 'medium' | 'large';
  outlined?: boolean;
  rounded?: boolean;
  icon?: React.ReactNode;
  onClick?: () => void;
  className?: string;
}

const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'primary',
  size = 'medium',
  outlined = false,
  rounded = false,
  icon,
  onClick,
  className = '',
}) => {
  const classNames = [
    'badge',
    `badge--${variant}`,
    `badge--${size}`,
    outlined && 'badge--outlined',
    rounded && 'badge--rounded',
    onClick && 'badge--clickable',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  const Component = onClick ? 'button' : 'span';

  return (
    <Component className={classNames} onClick={onClick}>
      {icon && <span className="badge__icon">{icon}</span>}
      <span className="badge__text">{children}</span>
    </Component>
  );
};

// Predefined badge variants for common use cases
export const StatusBadge: React.FC<{
  status: 'active' | 'inactive' | 'pending' | 'completed' | 'cancelled';
  size?: 'small' | 'medium' | 'large';
}> = ({ status, size = 'medium' }) => {
  const statusConfig = {
    active: { variant: 'success' as const, label: 'Active', icon: '●' },
    inactive: { variant: 'secondary' as const, label: 'Inactive', icon: '●' },
    pending: { variant: 'warning' as const, label: 'Pending', icon: '●' },
    completed: { variant: 'success' as const, label: 'Completed', icon: '✓' },
    cancelled: { variant: 'danger' as const, label: 'Cancelled', icon: '✕' },
  };

  const config = statusConfig[status];

  return (
    <Badge variant={config.variant} size={size} rounded>
      {config.icon} {config.label}
    </Badge>
  );
};

// Payment status badge
export const PaymentBadge: React.FC<{
  status: 'paid' | 'unpaid' | 'partial' | 'overdue';
  size?: 'small' | 'medium' | 'large';
}> = ({ status, size = 'medium' }) => {
  const statusConfig = {
    paid: { variant: 'success' as const, label: 'Paid' },
    unpaid: { variant: 'danger' as const, label: 'Unpaid' },
    partial: { variant: 'warning' as const, label: 'Partial' },
    overdue: { variant: 'danger' as const, label: 'Overdue' },
  };

  const config = statusConfig[status];

  return (
    <Badge variant={config.variant} size={size} rounded>
      {config.label}
    </Badge>
  );
};

// Appointment type badge
export const AppointmentTypeBadge: React.FC<{
  type: 'scheduled' | 'walkin' | 'emergency';
  size?: 'small' | 'medium' | 'large';
}> = ({ type, size = 'medium' }) => {
  const typeConfig = {
    scheduled: { variant: 'primary' as const, label: 'Scheduled' },
    walkin: { variant: 'warning' as const, label: 'Walk-in' },
    emergency: { variant: 'danger' as const, label: 'Emergency' },
  };

  const config = typeConfig[type];

  return (
    <Badge variant={config.variant} size={size}>
      {config.label}
    </Badge>
  );
};

export default Badge;