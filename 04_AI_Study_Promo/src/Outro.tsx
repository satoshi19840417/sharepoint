import { AbsoluteFill, useCurrentFrame, interpolate, useVideoConfig, spring } from 'remotion';

export const Outro = () => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();

    // Fade in text
    const opacity = interpolate(frame, [0, 30], [0, 1]);

    const logoScale = spring({
        fps,
        frame: frame - 20,
        config: { damping: 12, stiffness: 200 }
    });

    return (
        <AbsoluteFill className="text-white flex items-center justify-center">
            <div style={{ opacity }} className="text-center z-10">
                <h2 className="text-3xl mb-8 font-light tracking-[0.5em] text-cyan-300 drop-shadow-md">
                    UNLOCK THE POTENTIAL
                </h2>

                <div style={{ transform: `scale(${Math.max(0, logoScale)})` }} className="bg-white/10 p-10 rounded-3xl backdrop-blur-md border border-white/20 shadow-2xl">
                    <h1 className="text-7xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-purple-500 to-pink-500">
                        セルジェンテック
                    </h1>
                    <div className="w-full h-1 bg-gradient-to-r from-transparent via-white to-transparent my-6 opacity-50"></div>
                    <p className="text-2xl text-gray-300 font-mono">
                        AI Study Group
                    </p>
                </div>
            </div>

            {/* Subtle background gradient moving - reduced opacity for particles */}
            <AbsoluteFill className="-z-10 bg-gradient-to-br from-indigo-900/40 to-black/80" />
        </AbsoluteFill>
    );
};
