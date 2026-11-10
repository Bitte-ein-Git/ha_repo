import React from 'react'
import Link from 'next/link'
import Ipc from '../lib/ipc'

interface HeaderProps {
  hidden?: boolean;
  gamertag: string;
  level: number;
}

function Header({
    hidden = false,
    gamertag,
    level = 0,
}: HeaderProps) {

    const [headerLinks, setHeaderLinks] = React.useState([])
    const [mobileNavOpen, setMobileNavOpen] = React.useState(false)

    function createLinks(level){
        return (level > 1) ? [
            {
                name: 'My Consoles',
                title: 'View consoles',
                url: '/home',
                active: false,
            }, {
                name: 'xCloud Library',
                title: 'Browse xCloud library',
                url: '/xcloud/home',
                active: false,
            }, {
                name: 'Settings',
                title: 'Change application settings',
                url: '/settings/home',
                active: false,
            }, {
                name: gamertag,
                title: 'View profile',
                url: '/profile',
                active: false,
            },
        ] : [
            {
                name: 'My Consoles',
                title: 'View consoles',
                url: '/home',
                active: false,
            }, {
                name: 'Settings',
                title: 'Change application settings',
                url: '/settings/home',
                active: false,
            }, {
                name: gamertag,
                title: 'View profile',
                url: '/profile',
                active: false,
            },
        ]
    }

    function setMenuActive(id) {
        const links = createLinks(level)
        links[id].active = true
        setHeaderLinks(links)
        setMobileNavOpen(false)
        return null
    }

    function drawMenu() {
        const linksHtml = []

        for(const link in headerLinks){
            linksHtml.push(<li key={ link }>
                <Link legacyBehavior href={ headerLinks[link].url } key={ headerLinks[link].url }>
                    <a title={ headerLinks[link].title } onClick={ () => {
                        setMenuActive(link)
                    } } className={headerLinks[link].active === true ? 'active' : ''}>{ headerLinks[link].name }</a>
                </Link>
            </li>)
        }

        return linksHtml
    }

    function confirmQuit() {
        if(window.Greenlight && window.Greenlight.isWebUI && window.Greenlight.isWebUI() === true)
            return
    
        if(confirm('Are you sure you want to quit?')){
            Ipc.send('app', 'quit')
        }
    }

    function toggleMobileNav() {
        setMobileNavOpen(!mobileNavOpen)
    }

    React.useEffect(() => {
        if(headerLinks.length <= 0 && !isNaN(level)){
            const links = createLinks(level)
            links[0].active = true
            setHeaderLinks(links)
        }
    })

    React.useEffect(() => {
        function onResize() {
            if (window.innerWidth > 768) {
                setMobileNavOpen(false)
            }
        }
        window.addEventListener('resize', onResize)
        return () => window.removeEventListener('resize', onResize)
    }, [])
  
    const headerClass = [
        hidden === true ? 'disabled' : '',
        mobileNavOpen ? 'mobile-nav-open' : '',
    ].filter(Boolean).join(' ')

    return (
        <React.Fragment>
            <div id="component_header" className={headerClass}>
                <a onClick={ confirmQuit } id="actionBarLogo" title="Home">
                    <i className="fa-brands fa-xbox"></i>
                </a>

                <button
                    type="button"
                    className="mobile-menu-toggle"
                    aria-label="Toggle menu"
                    aria-expanded={mobileNavOpen}
                    onClick={toggleMobileNav}
                >
                    <i className={mobileNavOpen ? 'fa-solid fa-xmark' : 'fa-solid fa-bars'}></i>
                </button>

                <div className="mobile-nav-overlay" onClick={() => setMobileNavOpen(false)} />

                <ul className="menu">
                    { drawMenu() }
                </ul>
            </div>
        </React.Fragment>
    )
}

export default Header
