import EmailCard from '../components/EmailCard';
import { useState } from 'react';
import UserImage from '../assets/user-image.svg';
import AngleRight from '../assets/angle-right.svg';
import Scan from '../assets/scan.svg';
import Gear from '../assets/gear.svg';
import Hamburger from '../assets/hamburger.svg';
import Warning from '../assets/warning.svg';
import ThumbsUp from '../assets/thumbs-up.svg';

function Dashboard() {
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [isUserSettingsOpen, setIsUserSettingsOpen] = useState(false);
    const [emailText, setEmailText] = useState('');
    const [scanFullVerdict, setScanFullVerdict] = useState(null);

    const emails = [
        {id: 1, content: "Welcome to our service!", verdict: "Safe", explanation: "This is a safe email.", risk_level: "Low", date: "2024-06-01"},
        {id: 2, content: "You've won a million dollars!", verdict: "Phishing", explanation: "This is a phishing email.", risk_level: "High", date: "2024-06-02"},
        {id: 3, content: "Your account has been compromised.", verdict: "Phishing", explanation: "This is a phishing email.", risk_level: "High", date: "2024-06-03"},
        {id: 4, content: "Meeting scheduled for tomorrow.", verdict: "Safe", explanation: "This is a safe email.", risk_level: "Low", date: "2024-06-04"},
    ];

    const handleScan = (e) => {
        e.preventDefault();
        // setScanPicked(true);
        setScanFullVerdict(emails[0]);
    };

    const renameScan = (id) => {
        // Implement rename functionality here (e.g., show input to enter new name and update email title)
        alert(`Rename email with ID ${id}`);
    }

    const deleteEmail = (id) => {
        // Implement delete functionality here (e.g., make API call to delete email)
        alert(`Email with ID ${id} deleted!`);
    }

    return (
        <div className="dashboard">
            <div 
                className={`overlay ${isSidebarOpen ? 'active' : ''}`} 
                onClick={() => setIsSidebarOpen(false)}
            ></div>

            <div className={`off-screen-sidebar ${isSidebarOpen ? 'active' : ''}`}>
                <div className="sidebar-header">
                    <h2>Holmes</h2>
                    <h3 onClick={() => setIsSidebarOpen(false)}>⛌</h3>
                </div>
                <div className="sidebar-content">
                    <div className="sidebar-content-top">
                        <button className="new-scan" onClick={() => {
                            setScanFullVerdict(null);
                            setIsSidebarOpen(false);
                            setEmailText('');
                        }}>
                            <img src={Scan} alt="Scan" />
                            <p>New Scan</p>
                        </button>
                        <div className="history-search">
                            <input type="text" placeholder="Search history..." />
                        </div>
                        <div className="history-list">
                            <p>History</p>
                            {emails.map((email) => (
                                <EmailCard 
                                    key={email.id}
                                    email={email}
                                    setScanFullVerdict={setScanFullVerdict}
                                    setIsSidebarOpen={setIsSidebarOpen}
                                    renameEmail={renameScan}
                                    deleteEmail={deleteEmail}
                                />
                            ))}
                        </div>
                    </div>
                    <div className="sidebar-content-bottom">
                        <button className="settings">
                            <img src={Gear} alt="Settings" />
                            <p>Settings</p>
                        </button>
                        <button className="user-settings">
                            <div className="user-settings-left">
                                <div className="user-image"><img src={UserImage} alt="User" /></div>
                                <div className="username">John Doe</div>
                            </div>
                            <div className="arrow">
                                <img src={AngleRight} alt="Arrow" />
                            </div>
                        </button>
                    </div>
                </div>
            </div>

            {/* <div className="settings-menu">
                
            </div> */}

            <nav className={`nav ${scanFullVerdict ? 'risk-' + scanFullVerdict.risk_level.toLowerCase() : ''}`}>
                <div 
                    className={`ham-sidebar ${isSidebarOpen ? 'active' : ''}`} 
                    onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                >
                    <img src={Hamburger} alt="Hamburger" />
                </div>
            </nav>
            
            {!scanFullVerdict ? (
                <div className="main-page">
                    <form onSubmit={handleScan} className="scan">
                        <input 
                        type="text" 
                        placeholder="Paste email here to scan..." 
                        className="scan-input" 
                        value={emailText}
                        onChange={(e) => setEmailText(e.target.value)}
                        />
                        <button type="submit" className="scan-button">
                            <img src={Scan} alt="Scan" />
                        </button>
                    </form>
                </div>
            ) : (
                <div className={`verdict-page risk-${scanFullVerdict.risk_level.toLowerCase()}`}>
                    <div className="verdict-page-content">
                        <div className="verdict-page-content-header">
                            <button className="back-btn" onClick={() => {
                                setScanFullVerdict(null)
                                setEmailText(scanFullVerdict.content);
                            }}>&lt; Back</button>
                            <p>{scanFullVerdict.date}</p>
                        </div>
                        <div className="verdict-icon">
                            {scanFullVerdict.verdict === "Safe" ? (
                                <img src={ThumbsUp} alt="Safe" />
                            ) : (
                                <img src={Warning} alt="Danger" />
                            )}
                        </div>
                        <div className="verdict">{scanFullVerdict.verdict}</div>
                        <div className="verdict-risk-level">Risk Level: {scanFullVerdict.risk_level}</div>
                        <div className="verdict-explanation">{scanFullVerdict.explanation}</div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default Dashboard;