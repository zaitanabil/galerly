import React, { useState, useEffect } from 'react';

interface ProgressiveImageProps extends React.ImgHTMLAttributes<HTMLImageElement> {
  src: string;
  placeholderSrc?: string;
  className?: string;
}

export default function ProgressiveImage({ src, placeholderSrc, className, alt, ...props }: ProgressiveImageProps) {
  const [imgSrc, setImgSrc] = useState(placeholderSrc || src);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    // If no placeholder, just load the main image
    if (!placeholderSrc) {
      setImgSrc(src);
      return;
    }

    // Start with placeholder
    setImgSrc(placeholderSrc);
    setIsLoaded(false);

    // Load main image
    const img = new Image();
    img.src = src;
    img.onload = () => {
      setImgSrc(src);
      setIsLoaded(true);
    };
  }, [src, placeholderSrc]);

  return (
    <img
      src={imgSrc}
      alt={alt}
      className={`${className} transition-filter duration-500 ${
        isLoaded || !placeholderSrc ? 'blur-0' : 'blur-sm'
      }`}
      {...props}
    />
  );
}

