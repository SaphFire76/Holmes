import { createPortal } from 'react-dom';
import { useState, useRef } from 'react';
import MoreIcon from '../assets/images/more-horiz.svg';

function EmailCard({ email, onLoadDetails, setIsSidebarOpen, scanFullVerdict, isLoadingVerdict, isHistorySearchOpen, setIsHistorySearchOpen, renameScan, deleteScan }) {
    const [newTitle, setNewTitle] = useState("");
    const email_title = email.title.length > 28 ? email.title.substring(0, 25) + '...' : email.title;

    const formattedDate = new Date(email.date).toLocaleDateString('en-GB', {
        day: 'numeric',
        month: 'short'
    });

    const isSelected = scanFullVerdict && scanFullVerdict.scan_id === email.scan_id;

    const buttonRef = useRef(null);
    const [menuCoords, setMenuCoords] = useState({ top: 0, left: 0 });
    const [isMoreMenuOpen, setIsMoreMenuOpen] = useState(false);
    const [hoverMenuType, setHoverMenuType] = useState(null);

    const handleMoreMenu = () => {
        // Get the exact X/Y coordinates of the button on the screen
        const rect = buttonRef.current.getBoundingClientRect();
        setMenuCoords({
            top: rect.bottom, // Place menu just below the button
            left: rect.left   // Align to the left of the button (or use rect.right to align right)
        });
        setIsMoreMenuOpen(!isMoreMenuOpen);
    };

    return (
        <>
            <div className={`email-card ${isSelected ? 'selected' : ''}`}>
                <button className="email-title" onClick={async () => {
                    await onLoadDetails(email.scan_id);
                    if (!isLoadingVerdict) {
                        setIsHistorySearchOpen(false);
                        if (window.innerWidth < 1440) {
                            setIsSidebarOpen(false);
                        }
                    }
                }}>
                    {email_title}
                    {isHistorySearchOpen && (
                        <span>{formattedDate}</span>
                    )}
                </button>
                <div className="more">
                    <div className={`more-btn ${isMoreMenuOpen ? 'active' : ''}`} onClick={handleMoreMenu} ref={buttonRef}>
                        <button onClick={handleMoreMenu}>
                            <img src={MoreIcon} alt="More" />
                        </button>
                    </div>
                    {isMoreMenuOpen && createPortal (
                        <>
                            <div className="more-options-overlay" onClick={() => setIsMoreMenuOpen(false)}></div>
                            
                            <div 
                                className="more-options"
                                style={{ 
                                    position: 'fixed', // Must be fixed to use screen coordinates
                                    top: `${menuCoords.top}px`, 
                                    left: `${menuCoords.left}px` // Or calculate based on right side if preferred
                                }}
                            >
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
                        </>,
                        document.body
                    )}
                </div>
            </div>

            {hoverMenuType && (
                <div className="overlay2" onClick={() => setHoverMenuType(null)}>
                    <div className="hover-menu" onClick={(e) => e.stopPropagation()}>
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