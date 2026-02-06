import { AbsoluteFill, useVideoConfig, useCurrentFrame, interpolate, spring } from 'remotion';

export const Hook = () => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();

    // 0-90: Show AI and Skill separately
    // 90-120: They move towards center
    // 120: Collapse/Merge
    // 120-150: Explosion/Flash
    // 150+: Show Partner Agent

    const aiOpacity = interpolate(frame, [0, 20], [0, 1]);
    const skillOpacity = interpolate(frame, [40, 60], [0, 1]);

    // Move slightly floating before merge
    const float = Math.sin(frame / 20) * 10;

    // Merge animation
    const mergeProgress = interpolate(frame, [90, 120], [0, 1], { extrapolateRight: 'clamp' });
    const aiX = interpolate(mergeProgress, [0, 1], [-200, 0]);
    const skillX = interpolate(mergeProgress, [0, 1], [200, 0]);
    const elementsScale = interpolate(mergeProgress, [0, 1], [1, 0]); // Shrink as they hit center

    // Result animation
    const resultScale = spring({
        fps,
        frame: frame - 120,
        config: { damping: 12, stiffness: 100 }
    });
    const resultOpacity = interpolate(frame, [120, 130], [0, 1]);

    return (
        <AbsoluteFill className="flex items-center justify-center font-bold">
            {/* Initial Elements: AI & Skill */}
            <div style={{ transform: `translateX(${aiX}px) translateY(${float}px) scale(${elementsScale})`, opacity: aiOpacity }} className="absolute">
                <div className="bg-blue-600/80 p-8 rounded-full w-48 h-48 flex items-center justify-center backdrop-blur-md shadow-lg border-4 border-blue-400">
                    <span className="text-6xl text-white">AI</span>
                </div>
            </div>

            <div style={{ transform: `translateX(${skillX}px) translateY(${-float}px) scale(${elementsScale})`, opacity: skillOpacity }} className="absolute">
                <div className="bg-purple-600/80 p-8 rounded-full w-48 h-48 flex items-center justify-center backdrop-blur-md shadow-lg border-4 border-purple-400">
                    <span className="text-4xl text-white">スキル</span>
                </div>
            </div>

            {/* Plus sign */}
            <div style={{ opacity: interpolate(frame, [60, 90, 100], [0, 1, 0]) }} className="absolute text-6xl text-white">
                +
            </div>

            {/* Final Result: Partner Agent */}
            <div style={{ transform: `scale(${resultScale})`, opacity: resultOpacity }} className="z-20 text-center">
                <div className="bg-gradient-to-r from-amber-300 via-orange-400 to-red-500 p-1 rounded-2xl shadow-[0_0_50px_rgba(255,165,0,0.6)]">
                    <div className="bg-black/80 px-12 py-8 rounded-xl backdrop-blur-xl border border-white/20">
                        <h1 className="text-8xl text-transparent bg-clip-text bg-gradient-to-r from-amber-200 to-yellow-500 drop-shadow-sm mb-4">
                            相棒
                        </h1>
                        <p className="text-white text-2xl tracking-[0.8em] font-light">
                            AGENT
                        </p>
                    </div>
                </div>
            </div>

            {/* Impact Flash */}
            <AbsoluteFill
                style={{ opacity: interpolate(frame, [118, 120, 140], [0, 0.8, 0]) }}
                className="bg-white pointer-events-none mix-blend-overlay"
            />
        </AbsoluteFill>
    );
};
