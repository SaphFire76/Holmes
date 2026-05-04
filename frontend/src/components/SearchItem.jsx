import { useState } from 'react';
import MoreIcon from '../assets/more-horiz.svg';

function SearchItem({ email, onLoadDetails, setIsSidebarOpen, renameEmail, deleteEmail, scanFullVerdict }) {
    const [isMoreMenuOpen, setIsMoreMenuOpen] = useState(false);
    const email_title = email.title.length > 30 ? email.title.substring(0, 27) + '...' : email.title;

    const isSelected = scanFullVerdict && scanFullVerdict.scan_id === email.scan_id;

    return (
        <div className={`search-item ${isSelected ? 'selected' : ''}`}>
            <button className="search-item-title" onClick={() => {
                onLoadDetails(email.scan_id);
                setIsSidebarOpen(false);
            }}>
                {email_title}
            </button>
            <div className="search-item-more">
                <div className={`search-item-more-btn ${isMoreMenuOpen ? 'active' : ''}`} onClick={() => setIsMoreMenuOpen(!isMoreMenuOpen)}>
                    <button onClick={() => setIsMoreMenuOpen(!isMoreMenuOpen)}>
                        <img src={MoreIcon} alt="More" />
                    </button>
                </div>
                {isMoreMenuOpen && (
                    <>
                    <div className="search-item-more-options-overlay" onClick={() => setIsMoreMenuOpen(false)}></div>
                    
                    <div className="search-item-more-options">
                        <button
                            onClick={() => {
                                setIsMoreMenuOpen(false);
                                renameEmail(email.scan_id);
                        }}>
                            Rename
                        </button>
                        <button onClick={() => {
                            setIsMoreMenuOpen(false);
                            deleteEmail(email.scan_id);
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

export default SearchItem;