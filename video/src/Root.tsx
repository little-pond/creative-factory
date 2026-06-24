import { Composition } from "remotion";
import { CreativeFactoryDemo, DEMO_DURATION, FPS } from "./CreativeFactoryDemo";

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="CreativeFactoryDemo"
      component={CreativeFactoryDemo}
      durationInFrames={DEMO_DURATION}
      fps={FPS}
      width={1920}
      height={1080}
    />
  );
};
