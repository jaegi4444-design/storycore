type CharacterAvatarProps = {
  name: string;
  imageUrl?: string | null;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
};

const sizeClasses = {
  sm: 'h-10 w-10 text-sm',
  md: 'h-16 w-16 text-lg',
  lg: 'h-32 w-32 text-3xl',
};

export function CharacterAvatar({
  name,
  imageUrl,
  size = 'md',
  className = '',
}: CharacterAvatarProps) {
  const initial = name.trim().charAt(0) || '?';

  if (imageUrl) {
    return (
      <img
        src={imageUrl}
        alt={name}
        className={`rounded-xl object-cover ${sizeClasses[size]} ${className}`}
      />
    );
  }

  return (
    <div
      className={`flex items-center justify-center rounded-xl bg-accent/20 font-semibold text-accent-hover ${sizeClasses[size]} ${className}`}
      aria-hidden="true"
    >
      {initial}
    </div>
  );
}
