import { useState } from 'react';
import MoreIcon from '../assets/more-horiz.svg';

function EmailCard({ email, onLoadDetails, setIsSidebarOpen, scanFullVerdict, isHistorySearchOpen, renameScan, deleteScan }) {
    const [isMoreMenuOpen, setIsMoreMenuOpen] = useState(false);
    const [hoverMenuType, setHoverMenuType] = useState(null);
    const [newTitle, setNewTitle] = useState("");
    const email_title = email.title.length > 30 ? email.title.substring(0, 27) + '...' : email.title;

    const formattedDate = new Date(email.date).toLocaleDateString('en-GB', {
        day: 'numeric',
        month: 'short'
    });

    const isSelected = scanFullVerdict && scanFullVerdict.scan_id === email.scan_id;

    return (
        <>
            <div className={`email-card ${isSelected ? 'selected' : ''}`}>
                <button className="email-title" onClick={() => {
                    onLoadDetails(email.scan_id);
                    setIsSidebarOpen(false);
                }}>
                    {email_title}
                    {isHistorySearchOpen && (
                        <span>{formattedDate}</span>
                    )}
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
                                <button onClick={() => {
                                    setIsMoreMenuOpen(false);
                                    setHoverMenuType('rename');
                                }}>
                                    Rename
                                </button>
                                <button onClick={() => {
                                    setIsMoreMenuOpen(false);
                                    setHoverMenuType('delete');
                                }}>
                                    Delete
                                </button>
                            </div>
                        </>
                    )}
                </div>
            </div>

            {hoverMenuType && (
                <div className="overlay2">
                    <div className="hover-menu">
                        {hoverMenuType === 'rename' ? (
                            <>
                                <h2>Rename</h2>
                                <form onSubmit={async (e) => {
                                    e.preventDefault(); 
                                    await renameScan(email.scan_id, newTitle);
                                    setHoverMenuType(null);
                                    setNewTitle("");
                                }}>
                                    <input
                                        type="text"
                                        placeholder="Enter new name..."
                                        value={newTitle}
                                        onChange={(e) => setNewTitle(e.target.value)}
                                    />
                                    <div className="footer">
                                        <button type="button" onClick={() => setHoverMenuType(null)}>
                                            Cancel
                                        </button>
                                        <button type="submit">
                                            Save
                                        </button>
                                    </div>
                                </form>
                            </>
                        ) : (
                            <>
                                <h2>Delete</h2>
                                <p>Are you sure you want to delete this email?</p>
                                <div className="footer">
                                    <button onClick={() => setHoverMenuType(null)}>Cancel</button>
                                    <button onClick={async () => {
                                        await deleteScan(email.scan_id);
                                        setHoverMenuType(null);
                                    }}>Delete</button>
                                </div>
                            </>
                        )}
                    </div>
                </div>
            )}
        </>
    );
}

export default EmailCard;