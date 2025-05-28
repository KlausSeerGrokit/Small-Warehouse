import { ParacordClient, PncpCallResponse } from "@grokit-data/paracord-panels-interface";
// import styles from './Controls.module.scss';
import { useEffect, useState } from "react";
import { ObservationCallbackObject, PncpMessageCallbackObject, PncpMessageKind, PncpRequestCallbackObject } from "@grokit-data/paranet-client";
import SkillButton from "./SkillButton";

interface ControlsProps {
    client: ParacordClient
}

// interface Skill {
//     subject: string,
//     action: string,
//     body: any
// }

const Controls: React.FC<ControlsProps> = ({ client }) => {

    // const skills: Skill[] = [
    //     {subject: "demo", action: "start_demo", body: {}},
    //     {subject: "ur_arm_phy", action: "fill_tote", body: {}},
    //     {subject: "ur_digit", action: "stage_tote", body: {target: "good"}},
    // ];

    const [latestPncp, setLatestPncp] = useState<PncpMessageCallbackObject | null>(null);
    const [latestObs, setLatestObs] = useState<PncpRequestCallbackObject | null>(null);

    useEffect(() => {
        (async () => {
            // for (const skill of skills) {
            //     await client.registerObserverCallback({ subject: skill.subject, action: skill.action });
            // }
            client.messageCallback((msg: PncpMessageCallbackObject) => {
                console.log("GOT MSG CALLBACK", msg);
                if (msg.message.body.type == PncpMessageKind.PNCP_RESPONSE) {
                    setLatestPncp(msg);
                }
            });
            client.observationCallback((msg: ObservationCallbackObject) => {
                console.log("GOT OBS CALLBACK", msg);
                if (msg.message.type == "skill") {
                    setLatestObs(msg.message);
                }
            });
        })();
    }, []);

    return (
      <div>
        <SkillButton subject="demo" action="start_demo" client={client} />
        <SkillButton subject="ur_arm_phy" action="fill_tote" client={client} />
        <SkillButton subject="digit_phy" action="stage_tote" body={{target: "good"}} client={client} />

        {latestPncp && (
          <div>
            <p>
              Actor response:{" "}
              {JSON.stringify(latestPncp.message.body.value.data)}
            </p>
          </div>
        )}
        {latestObs && (
          <div>
            <p>
              Observed: {latestObs.body.subject}/{latestObs.body.action} :{" "}
              {JSON.stringify(latestObs.body.body)}
            </p>
          </div>
        )}
      </div>
    );
  };
  

  export default Controls;
  