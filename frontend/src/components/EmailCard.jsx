import { useState } from 'react';
import MoreIcon from '../assets/more-horiz.svg';

function EmailCard({ email, setScanFullVerdict, setIsSidebarOpen, renameEmail, deleteEmail }) {
    const [isMoreMenuOpen, setIsMoreMenuOpen] = useState(false);
    const email_title = email.content.length > 20 ? email.content.substring(0, 20) + '...' : email.content;

    return (
        <div className="email-card">
            <button className="email-title" onClick={() => {
                setScanFullVerdict(email);
                setIsSidebarOpen(false);
            }}>
                {email_title}
            </button>
            <div className="more">
                <div className={`more-btn ${isMoreMenuOpen ? 'active' : ''}`} onClick={() => setIsMoreMenuOpen(!isMoreMenuOpen)}>
                    <button onClick={() => setIsMoreMenuOpen(!isMoreMenuOpen)}>
                        <img src={MoreIcon} alt="More" />
                    </button>
                </div>
                {isMoreMenuOpen && (
                    <>
                    <div className="more-options-overlay" onClick={() => setIsMoreMenuOpen(false)}></div>
                    
                    <div className="more-options">
                        <button
                            onClick={() => {
                                setIsMoreMenuOpen(false);
                                renameEmail(email.id);
                        }}>
                            Rename
                        </button>
                        <button onClick={() => {
                            setIsMoreMenuOpen(false);
                            deleteEmail(email.id);
                        }}>
                            Delete
                        </button>
                    </div>
                    </>
                )}
            </div>
        </div>
    );
}

export default EmailCard;