import React from 'react';

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';


const styles = {
    heart: {color: 'red'}
}

class Footer extends React.Component {

    render() {
        return (
            <div>
                <ul className="nav justify-content-center">
                    <li className="nav-item text-center">
                        <a className='nav-link disabled' href='/'>
                            <b>Made with <FontAwesomeIcon icon='heart' style={styles.heart}/> in Dublin, Ireland</b>
                        </a>
                    </li>
                </ul>
            </div>
        )
    }
}

export default Footer;