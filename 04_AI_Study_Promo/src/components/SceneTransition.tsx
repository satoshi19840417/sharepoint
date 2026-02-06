
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import React from 'react';

type TransitionType = 'slide' | 'fade' | 'none';

export const SceneTransition: React.FC<{
    children: React.ReactNode;
    enterProgress?: number; // 0 to 1
    exitProgress?: number; // 0 to 1
    type?: TransitionType;
}> = ({ children, enterProgress = 1, exitProgress = 0, type = 'fade' }) => {

    // Enter animation (0 -> 1)
    // When entering, we want to go from invisible/offset to visible/centered.
    // If enterProgress is 0 (start), opacity should be 0. If 1 (end), opacity 1.

    // Exit animation (0 -> 1)
    // When exiting, we want to go from visible to invisible.

    const opacity = interpolate(
        enterProgress,
        [0, 1],
        [0, 1],
        { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
    ) * interpolate(
        exitProgress,
        [0, 1],
        [1, 0],
        { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
    );

    const translateY = interpolate(
        enterProgress,
        [0, 1],
        [50, 0], // Slide up from 50px down
        { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
    ) + interpolate(
        exitProgress,
        [0, 1],
        [0, -50], // Slide up to -50px
        { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
    );

    const scale = interpolate(
        enterProgress,
        [0, 1],
        [0.9, 1],
        { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
    ) * interpolate(
        exitProgress,
        [0, 1],
        [1, 0.9],
        { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
    );

    if (type === 'none') {
        return <AbsoluteFill>{children}</AbsoluteFill>;
    }

    return (
        <AbsoluteFill
            style={{
                opacity,
                transform: `translateY(${translateY}px) scale(${scale})`,
            }}
        >
            {children}
        </AbsoluteFill>
    );
};
