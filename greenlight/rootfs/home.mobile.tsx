import React from 'react'
import Head from 'next/head'
import Link from 'next/link'
import Ipc from '../lib/ipc'
import { useQuery } from 'react-query'

import Button from '../components/ui/button'
import Label from '../components/ui/label'
import Loader from '../components/ui/loader'

function powerLabel(state: string) {
    if (state === 'On') return { text: 'On', cls: 'green' }
    if (state === 'ConnectedStandby') return { text: 'Standby', cls: 'orange' }
    return { text: state || 'Unknown', cls: '' }
}

function Home() {
    const consoles = useQuery('consoles', () => Ipc.send('consoles', 'get'), { staleTime: 60 * 1000 })

    return (
        <React.Fragment>
            <Head>
                <title>RemotePlay – Consoles</title>
            </Head>

            <div className="rp-page rp-consoles">
                <h1 className="rp-page-title">My Consoles</h1>
                <p className="rp-page-sub">Start remote play on a console</p>

                {consoles.isLoading === true ? (
                    <div className="rp-loader-wrap"><Loader /></div>
                ) : consoles.isFetched === true && consoles.data && consoles.data.length > 0 ? (
                    <div className="rp-console-list">
                        {consoles.data.map((item: any, i: number) => {
                            const canStream = item.remoteManagementEnabled === true && item.consoleStreamingEnabled === true
                            const power = powerLabel(item.powerState)
                            return (
                                <div className="rp-console-card" key={item.id || i}>
                                    <div className="rp-console-icon">
                                        <i className="fa-brands fa-xbox"></i>
                                    </div>
                                    <div className="rp-console-body">
                                        <h2 className="rp-console-name">{item.name}</h2>
                                        <p className="rp-console-id">{item.id}</p>
                                        <div className="rp-console-meta">
                                            {canStream ? (
                                                <Label className={power.cls}>{power.text}</Label>
                                            ) : (
                                                <Label className="orange">Setup needed</Label>
                                            )}
                                        </div>
                                        {!canStream && (
                                            <p className="rp-console-warn">
                                                {!item.remoteManagementEnabled && 'Remote management off. '}
                                                {!item.consoleStreamingEnabled && 'Console streaming off.'}
                                            </p>
                                        )}
                                        <div className="rp-console-actions">
                                            <Link href={`stream/${item.id}?name=${encodeURIComponent(item.name || item.id)}`}>
                                                <Button label="Start Remote Play" className="btn-primary rp-btn-full" />
                                            </Link>
                                        </div>
                                    </div>
                                </div>
                            )
                        })}
                    </div>
                ) : (
                    <div className="rp-empty">
                        <i className="fa-brands fa-xbox"></i>
                        <p>No consoles found.</p>
                        <p className="rp-empty-hint">
                            Enable remote play on your Xbox and make sure it shows up in the official Xbox app.
                        </p>
                    </div>
                )}
            </div>
        </React.Fragment>
    )
}

export default Home
