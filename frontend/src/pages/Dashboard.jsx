import EmailCard from '../components/EmailCard';
import { useState, useEffect, useRef, useLayoutEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { fetchUserDetails, fetchHistory, fetchFullScanVerdict, scanNewEmail, searchScanHistory, renameScanApi, deleteScanApi } from '../services/scanService';
import { useNavigate } from 'react-router-dom';
import UserImage from '../assets/images/user-image.svg';
import AngleRight from '../assets/images/angle-right.svg';
import Scan from '../assets/images/scan.svg';
import Gear from '../assets/images/gear.svg';
import Hamburger from '../assets/images/hamburger.svg';
import Warning from '../assets/images/warning.svg';
import ThumbsUp from '../assets/images/thumbs-up.svg';
import Search from '../assets/images/search.svg';
import Back from '../assets/images/back.svg';
import DoubleArrow from '../assets/images/double-arrow.svg';
import Loading from '../assets/images/loading.svg';
import Logout from '../assets/images/logout.svg';

function Dashboard() {
    const navigate = useNavigate();

    const [isSidebarOpen, setIsSidebarOpen] = useState(() => {
        if (typeof window !== 'undefined') {
            return window.innerWidth >= 1440;
        }
        return false;
    });

    const [isUserSettingsOpen, setIsUserSettingsOpen] = useState(false);
    const [isHistorySearchOpen, setIsHistorySearchOpen] = useState(false);
    const [hoverMenuType, setHoverMenuType] = useState(null);
    const [emailText, setEmailText] = useState('');
    const [historySearchTerm, setHistorySearchTerm] = useState('');
    const [scanFullVerdict, setScanFullVerdict] = useState(null);

    const [isExpanded, setIsExpanded] = useState(false);

    // This watches the emailText. Every time they type, it checks the height!
    useLayoutEffect(() => {
        if (textareaRef.current) {
            // Grab the physical height of the textarea in pixels
            const currentHeight = textareaRef.current.offsetHeight;
            
            // A single line with your 1em padding is usually around 50-55px tall.
            // If it grows taller than 60px, we know it has wrapped to a second line!
            if (currentHeight > 60) {
                setIsExpanded(true);
            } else {
                setIsExpanded(false);
            }
        }
    }, [emailText]); // Re-run this check every time the text changes

    const textareaRef = useRef(null);

    const handleTextChange = (e) => {
        setEmailText(e.target.value);
        
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
        }
    };

    const [userData, setUserData] = useState(null);
    const [scanHistory, setScanHistory] = useState([]);
    const [error, setError] = useState(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const loadData = async () => {
            try {
                // Fire both API calls simultaneously 
                const [userInfo, historyData] = await Promise.all([
                    fetchUserDetails(),
                    fetchHistory()
                ]);

                setUserData(userInfo);
                setScanHistory(historyData);
            } catch (error) {
                console.error("Failed to fetch dashboard data:", error);
                setError("Failed to load dashboard. Please try again later.");
            } finally {
                setIsLoading(false);
            }
        };

        loadData();
    }, []); // Empty array means "run once on load"

    // Logout function to clear the token and redirect to login page
    const handleLogout = () => {
        // 1. Destroy the token
        localStorage.removeItem('access_token');
        
        // 2. Kick them out to the login page
        navigate('/login', { replace: true }); // 'replace: true' prevents them from using the back button!
    };

    const handleHistoryClick = async (scanId) => {
        try {
            // You could even add a 'setIsLoadingVerdict(true)' here if you wanted a spinner!
            const fullVerdict = await fetchFullScanVerdict(scanId);
            
            // Update the state with the FULL database row
            setScanFullVerdict(fullVerdict);
        } catch (error) {
            console.error("Failed to load details:", error);
        }
    };

    const [isScanning, setIsScanning] = useState(false);

    const handleScan = async (e) => {
        console.log("Initiating scan for email:", emailText);
        e.preventDefault();
        if (!emailText.trim()) return;

        try {
            setIsScanning(true);

            const newScanResult = await scanNewEmail(emailText);

            console.log("Received new scan result:", newScanResult);

            setScanFullVerdict(newScanResult);
            setScanHistory([newScanResult, ...scanHistory]);
            setEmailText("");

        } catch (error) {
            console.error("Failed to scan email:", error);
            // Handle error state here for an error UI banner
            
        } finally {
            // Turn OFF the loading state in the finally block!
            setIsScanning(false);
        }
    };

    const [searchResults, setSearchResults] = useState([]);
    const [isSearching, setIsSearching] = useState(false);

    useEffect(() => {
        const delaySearch = setTimeout(async () => {
            if (historySearchTerm.trim() !== '') {
                try {
                    setIsSearching(true);

                    console.log("Searching for:", historySearchTerm);
                    
                    // Call the backend
                    const results = await searchScanHistory(historySearchTerm);
                    
                    // Save the results to our new state
                    setSearchResults(results);
                } catch (error) {
                    console.error("Search failed:", error);
                } finally {
                    setIsSearching(false);
                }
            } else {
                // If the user clears the search box, clear the results!
                setSearchResults([]);
            }
        }, 500);

        return () => clearTimeout(delaySearch);

    }, [historySearchTerm]);


    const renameScan = async (id, newTitle) => {
        // 1. Prevent empty names
        if (!newTitle || newTitle.trim() === '') return;

        try {
            console.log(`Renaming scan ${id} to "${newTitle}"`);

            // 2. Tell the database to update it
            const data = await renameScanApi(id, newTitle);
            const updatedTitle = data.new_title;

            // 3. Update the main sidebar history instantly
            setScanHistory((prevHistory) => 
                prevHistory.map((scan) => 
                    scan.scan_id === id ? { ...scan, title: updatedTitle } : scan
                )
            );

            // 4. Update the search results (if the user is currently searching)
            setSearchResults((prevResults) => 
                prevResults.map((scan) => 
                    scan.scan_id === id ? { ...scan, title: updatedTitle } : scan
                )
            );

            // 5. Update the main view if the renamed email is currently selected!
            if (scanFullVerdict && scanFullVerdict.scan_id === id) {
                setScanFullVerdict({ ...scanFullVerdict, title: updatedTitle });
            }

        } catch (error) {
            console.error("Failed to rename scan:", error);
        }
    };

    const deleteScan = async (id) => {
        try {
            // 1. Tell the database to delete it permanently
            await deleteScanApi(id);

            // 2. Remove it from the main sidebar history instantly
            setScanHistory((prevHistory) => 
                prevHistory.filter((scan) => scan.scan_id !== id)
            );

            // 3. Remove it from the search results (if the user is currently searching)
            setSearchResults((prevResults) => 
                prevResults.filter((scan) => scan.scan_id !== id)
            );

            // 4. IMPORTANT: If the user is currently looking at the email they just deleted, clear the screen!
            if (scanFullVerdict && scanFullVerdict.scan_id === id) {
                setScanFullVerdict(null);
            }

        } catch (error) {
            console.error("Failed to delete scan:", error);
        }
    };

    if (isLoading || !userData) {
        return (
            <div className="loading-screen">
                <img src={Loading} alt="Loading"></img>
            </div>
        );
    }

    return (
        <div className="dashboard">
            <div 
                className={`overlay ${isSidebarOpen ? 'active' : ''}`} 
                onClick={() => setIsSidebarOpen(false)}
            ></div>

            <div className={`off-screen-sidebar ${isSidebarOpen ? 'active' : ''}`}>
                <div className="sidebar-header">
                    <h1>HOLMES</h1>
                    <img src={DoubleArrow} alt="Close Sidebar" onClick={() => setIsSidebarOpen(false)} />
                </div>
                <div className="sidebar-content">
                    <div className="sidebar-content-top">
                        <button className="new-scan" onClick={() => {
                            setScanFullVerdict(null);
                            if (window.innerWidth < 1440) {
                                setIsSidebarOpen(false);
                            }
                            setEmailText('');
                        }}>
                            <img src={Scan} alt="Scan" />
                            <p>New Scan</p>
                        </button>
                        <button className="history-search" onClick={() => {
                            setScanFullVerdict(null);
                            setIsSidebarOpen(false);
                            setIsHistorySearchOpen(true);
                        }}>
                            <img src={Search} alt="Search" />
                            Search History...
                        </button>
                        <div className="history-list">
                            <p>History</p>
                            {scanHistory.map((scan) => (
                                <EmailCard 
                                    className="recent-scans"
                                    key={scan.scan_id}
                                    email={scan}
                                    onLoadDetails={handleHistoryClick}
                                    setIsSidebarOpen={setIsSidebarOpen}
                                    setHoverMenuType={setHoverMenuType}
                                    scanFullVerdict={scanFullVerdict}
                                    isHistorySearchOpen={isHistorySearchOpen}
                                    renameScan={renameScan}
                                    deleteScan={deleteScan}
                                />
                            ))}
                        </div>
                    </div>
                    <div className="sidebar-content-bottom">
                        {/* <button className="settings">
                            <img src={Gear} alt="Settings" />
                            <p>Settings</p>
                        </button> */}
                        <button className="logout" onClick={handleLogout}>
                            <img src={Logout} alt="Logout" />
                            Log out
                        </button>
                        <button className="user-settings">
                            <div className="user-image"><img src={UserImage} alt="User" /></div>
                            <div className="user-text-info">
                                <div className="username">{userData.username}</div>
                                <div className="email-address">{userData.email}</div>
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
                <h1>HOLMES</h1>
            </nav>
            
            {!scanFullVerdict ? (
                <div className={`main-page ${isSidebarOpen ? 'sidebar-open' : ''}`}>
                    <div className="welcome-text">
                        <p>Hello 👋 ,</p>
                        <p>Found something phishy? 🎣</p>
                        <ul>
                            <li>Paste the email below to scan it.</li>
                            <li>For best results, include the entire email.</li>
                            <li>For even better results, include the email headers.</li>
                        </ul>
                    </div>
                    <form onSubmit={handleScan} className={`scan ${isExpanded ? 'expanded' : ''}`}>
                        <textarea 
                            ref={textareaRef}
                            placeholder="Paste away!" 
                            className={`scan-input ${isExpanded ? 'expanded' : ''}`} 
                            value={emailText}
                            onChange={handleTextChange}
                            disabled={isScanning}
                            rows={1}
                        />
                        <div className={`scan-button ${isExpanded ? 'expanded' : ''}`}>
                            <button 
                                type="submit" 
                                className={`scan-btn ${isScanning ? 'loading' : ''}`}
                                disabled={isScanning}
                            >
                                {isScanning ? (
                                    <img src={Loading} alt="Loading" />
                                ) : (
                                    <img src={Scan} alt="Scan" />
                                )}
                            </button>
                        </div>
                    </form>
                </div>
            ) : (
                <div className={`verdict-page risk-${scanFullVerdict.risk_level.toLowerCase()} ${isSidebarOpen ? 'sidebar-open' : ''}`}>
                    <div className="verdict-page-content">
                        <div className="verdict-page-content-header">
                            <button className="back-btn" onClick={() => {
                                setEmailText(scanFullVerdict.email);
                                setScanFullVerdict(null);
                            }}>&lt; Back</button>
                            <p>{scanFullVerdict.date}</p>
                        </div>
                        <div className="verdict-icon">
                            {scanFullVerdict.is_phishing ? (
                                <img src={Warning} alt="Danger" />
                            ) : (
                                <img src={ThumbsUp} alt="Safe" />
                            )}
                        </div>
                        <div className="verdict">{scanFullVerdict.is_phishing ? (
                                "Phishing"
                            ) : (
                                "Safe"
                            )}
                        </div>
                        <div className="verdict-risk-level">Risk Level: {scanFullVerdict.risk_level}</div>
                        <div className="verdict-explanation">{scanFullVerdict.explanation}</div>
                    </div>
                </div>
            )}

            {isHistorySearchOpen && (
                <div className="history-search-page">
                    <div className="history-search-header">
                        <div className="history-search-header-content">
                            <button className="back-btn" onClick={() => setIsHistorySearchOpen(false)}>
                                <img src={Back} alt="Back" />
                            </button>
                            <input 
                                type="text" 
                                placeholder="Search scan history..." 
                                value={historySearchTerm}
                                onChange={(e) => setHistorySearchTerm(e.target.value)}
                            />
                        </div>
                    </div>
                    <div className="history-search-results">
                        {historySearchTerm.trim() === '' ? (
                            
                            /* STATE 1: Search box is empty -> Show the full history */
                            scanHistory.map((scan) => (
                                <EmailCard 
                                    className="recent-scans"
                                    key={scan.scan_id}
                                    email={scan}
                                    onLoadDetails={handleHistoryClick}
                                    setIsSidebarOpen={setIsSidebarOpen}
                                    setHoverMenuType={setHoverMenuType}
                                    scanFullVerdict={scanFullVerdict}
                                    isHistorySearchOpen={isHistorySearchOpen}
                                    renameScan={renameScan}
                                    deleteScan={deleteScan}
                                />
                            ))
                            
                        ) : isSearching ? (
                            
                            /* STATE 2: Waiting for the backend -> Show loading text */
                            <p className="loading-text">Searching...</p>
                            
                        ) : searchResults.length === 0 ? (
                            
                            /* STATE 3: Backend finished, but returned empty array -> Show error text */
                            <p className="no-results-text">No emails found matching "{historySearchTerm}"</p>
                            
                        ) : (
                            
                            /* STATE 4: Backend finished and found matches -> Show search results */
                            searchResults.map((scan) => (
                                <EmailCard 
                                    className="recent-scans"
                                    key={scan.scan_id}
                                    email={scan}
                                    onLoadDetails={handleHistoryClick}
                                    setIsSidebarOpen={setIsSidebarOpen}
                                    setHoverMenuType={setHoverMenuType}
                                    scanFullVerdict={scanFullVerdict}
                                    isHistorySearchOpen={isHistorySearchOpen}
                                    renameScan={renameScan}
                                    deleteScan={deleteScan}
                                />
                            ))
                            
                        )}
                    </div>
                </div>
            )}

            
        </div>
    );
}

export default Dashboard;