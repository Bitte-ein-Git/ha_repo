import React from 'react'
import Link from 'next/link'
import { useRouter } from 'next/router'
import Ipc from '../lib/ipc'

interface HeaderProps {
  hidden?: boolean;
  gamertag: string;
  level: number;
}

function Header({
    hidden = false,
    gamertag,
}: HeaderProps) {
    const router = useRouter()
    const path = router.pathname || ''

    const isConsoles = path === '/home' || path.startsWith('/stream')
    const isSettings = path.startsWith('/settings') || path.startsWith('/profile')

    function confirmQuit() {
        if (window.Greenlight && window.Greenlight.isWebUI && window.Greenlight.isWebUI() === true)
            return
        if (confirm('Are you sure you want to quit?')) {
            Ipc.send('app', 'quit')
        }
    }

    if (hidden) return null

    return (
        <React.Fragment>
            <div id="component_header" className="rp-topbar">
                <a onClick={confirmQuit} id="actionBarLogo" title="Home" className="rp-logo">
                    <i className="fa-brands fa-xbox"></i>
                </a>
                <div className="rp-topbar-title">RemotePlay</div>
                <div className="rp-topbar-user" title={gamertag || ''}>
                    <span className="rp-gamertag">{gamertag || ''}</span>
                </div>
            </div>

            <nav id="rp_bottom_nav" className="rp-bottom-nav" aria-label="Main">
                <Link legacyBehavior href="/home">
                    <a className={isConsoles ? 'active' : ''} title="Consoles">
                        <i className="fa-solid fa-gamepad"></i>
                        <span>Consoles</span>
                    </a>
                </Link>
                <Link legacyBehavior href="/settings/home">
                    <a className={isSettings ? 'active' : ''} title="Settings">
                        <i className="fa-solid fa-gear"></i>
                        <span>Settings</span>
                    </a>
                </Link>
            </nav>
        </React.Fragment>
    )
}

export default Header
