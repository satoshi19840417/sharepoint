
import { AbsoluteFill, random, useCurrentFrame, useVideoConfig } from 'remotion';
import React, { useMemo } from 'react';

export const BackgroundParticles: React.FC<{
    count?: number;
    baseColor?: string;
}> = ({ count = 50, baseColor = 'rgba(255, 255, 255, 0.1)' }) => {
    const frame = useCurrentFrame();
    const { height, width } = useVideoConfig();

    const particles = useMemo(() => {
        return new Array(count).fill(true).map((_, i) => {
            const seed = i;
            const x = random(seed) * width;
            const size = random(seed + 1) * 20 + 5; // 5px to 25px
            const speed = random(seed + 2) * 2 + 0.5; // 0.5 to 2.5 px/frame
            const opacity = random(seed + 3) * 0.5 + 0.1; // 0.1 to 0.6
            return { x, size, speed, opacity, seed };
        });
    }, [count, width]);

    return (
        <AbsoluteFill className="bg-[conic-gradient(at_bottom_left,_var(--tw-gradient-stops))] from-slate-900 via-purple-900 to-slate-900 overflow-hidden">
            <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-10 mix-blend-overlay"></div>
            {particles.map((p, i) => {
                const y = (frame * p.speed) % (height + p.size);
                // Move from bottom to top
                const actualY = height - y;

                return (
                    <div
                        key={i}
                        className="rounded-full blur-[1px]"
                        style={{
                            position: 'absolute',
                            left: p.x,
                            top: actualY,
                            width: p.size,
                            height: p.size,
                            borderRadius: '50%',
                            backgroundColor: baseColor,
                            opacity: p.opacity,
                            transform: `translateY(${p.size}px)`, // Adjust for rendering off-screen
                        }}
                    />
                );
            })}
        </AbsoluteFill>
    );
};
