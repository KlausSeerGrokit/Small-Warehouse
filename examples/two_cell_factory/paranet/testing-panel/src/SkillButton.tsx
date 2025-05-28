import { ParacordClient, PncpCallResponse } from "@grokit-data/paracord-panels-interface";
import { SetStateAction, useEffect, useRef, useState } from "react";
import { Button, Spinner } from "react-bootstrap";
// import styles from './SkillButton.module.scss';
import Overlay from 'react-bootstrap/Overlay';
import Popover from 'react-bootstrap/Popover';

interface SkillButtonProps {
    client: ParacordClient
    subject: string;
    action: string;
    body?: any;
}
  
const SkillButton: React.FC<SkillButtonProps> = ({ client, subject, action, body = {}}) => {
    const [latestResponse, setLatestResponse] = useState<PncpCallResponse | null>(null);
    // useEffect(() => {
    //     (async () => {
    //         await client.registerObserverCallback({subject, action, callback: () => {
    //             console.log("SKILL BUTTON CALLBACK");
    //         }})
    //     })();
    // }, []);

    const [show, setShow] = useState(false);
    const [target, setTarget] = useState(null);
    const ref = useRef(null);

    const handleClick = (event: any) => {
        setShow(!show);
        setTarget(event.target);
      };

    async function sendRequest(event: any) {
      const response = await client.pncpRequest({subject, action, body });
      setLatestResponse(response);
      setShow(!show);
      setTarget(event.target);
    }

    return (
        <div >
            {/* <button onClick={sendRequest}>
                {subject} / {action} {latestResponse?.messageId || ""}
            </button> */}
            <div ref={ref}>
            <Button onClick={sendRequest}>{subject} / {action}</Button>

            <Overlay
                show={show}
                target={target}
                placement="right"
                container={ref}
                containerPadding={20}
            >
                <Popover id="popover-contained">
                <Popover.Header as="h3">{latestResponse?.messageId}</Popover.Header>
                <Popover.Body>
                    <Spinner/>
                </Popover.Body>
                </Popover>
            </Overlay>
            </div>
        </div>
    );
};

export default SkillButton;
