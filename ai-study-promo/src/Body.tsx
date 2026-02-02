import { AbsoluteFill, useCurrentFrame, spring, useVideoConfig, interpolate } from 'remotion';

// Keyword Component
const Keyword = ({ text, x, y, activationFrame, orbX, orbY }: { text: string, x: number, y: number, activationFrame: number, orbX: number, orbY: number }) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();

    // Activation logic: slightly before the orb hits (simulated by frame for simplicity in this version)
    // Or simpler: activate when frame > activationFrame
    const isActive = frame > activationFrame;

    const scale = spring({
        fps,
        frame: frame - activationFrame,
        config: { damping: 10, stiffness: 200 }
    });

    // Color transition
    const color = isActive ? 'text-cyan-400 drop-shadow-[0_0_15px_rgba(34,211,238,0.8)]' : 'text-gray-600';
    const bg = isActive ? 'bg-cyan-900/40 border-cyan-500' : 'bg-gray-800/20 border-gray-700';

    return (
        <div
            style={{
                left: x,
                top: y,
                transform: `scale(${isActive ? scale : 1})`,
                position: 'absolute'
            }}
            className={`transition-colors duration-300 ${color} ${bg} px-8 py-4 rounded-xl border-2 font-bold text-4xl shadow-xl backdrop-blur-sm`}
        >
            {text}
        </div>
    );
};

export const Body = () => {
    const frame = useCurrentFrame();
    const { width, height } = useVideoConfig();

    // Orb animation path (Bezier or simple interpolation)
    // Runs from frame 60 to 120
    const progress = interpolate(frame, [60, 120], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

    // Path: Bottom Left -> Top Right zigzag or curve
    const orbX = interpolate(progress, [0, 0.3, 0.7, 1], [-100, width * 0.4, width * 0.6, width + 100]);
    const orbY = interpolate(progress, [0, 0.3, 0.7, 1], [height + 100, height * 0.2, height * 0.8, -100]);

    // Final Impact Text
    const finalTextOpacity = interpolate(frame, [130, 150], [0, 1]);
    const finalTextScale = interpolate(frame, [130, 150], [2, 1], { extrapolateRight: 'clamp' });

    return (
        <AbsoluteFill className="items-center justify-center">
            {/* Keywords Grid - positions are relative % or px */}
            <div className="relative w-full h-full">
                <Keyword text="文献調査" x={100} y={200} activationFrame={65} orbX={orbX} orbY={orbY} />
                <Keyword text="データ分析" x={width - 400} y={250} activationFrame={75} orbX={orbX} orbY={orbY} />
                <Keyword text="報告書作成" x={200} y={500} activationFrame={90} orbX={orbX} orbY={orbY} />
                <Keyword text="コーディング" x={width - 500} y={600} activationFrame={100} orbX={orbX} orbY={orbY} />
            </div>

            {/* The Skill Orb */}
            {progress > 0 && progress < 1 && (
                <div
                    style={{ left: orbX, top: orbY, position: 'absolute' }}
                    className="w-20 h-20 rounded-full bg-white shadow-[0_0_40px_rgba(255,255,255,1)] z-20"
                />
            )}

            {/* Final Text */}
            <AbsoluteFill className="items-center justify-center pointer-events-none">
                <div style={{ opacity: finalTextOpacity, transform: `scale(${finalTextScale})` }} className="text-center z-30">
                    <h1 className="text-9xl font-black text-transparent bg-clip-text bg-gradient-to-br from-white via-cyan-100 to-blue-200 drop-shadow-[0_0_30px_rgba(255,255,255,0.5)]">
                        すべてを<br />変える
                    </h1>
                </div>
            </AbsoluteFill>
        </AbsoluteFill>
    );
};
