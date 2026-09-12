import React, {SyntheticEvent, useEffect, useState} from 'react';
import Wrapper from "./Wrapper";
import {Navigate, useParams} from 'react-router-dom';
import {Product} from "../interfaces/product";
import {ADMIN_API_URL} from "../config";

const ProductsEdit = () => {
    const {id} = useParams<{id: string}>();
    const [title, setTitle] = useState('');
    const [image, setImage] = useState('');
    const [redirect, setRedirect] = useState(false);

    useEffect(() => {
        (
            async () => {
                const response = await fetch(`${ADMIN_API_URL}/api/products/${id}`);

                const product: Product = await response.json();

                setTitle(product.title);
                setImage(product.image)
            }
        )();
    }, [id]);

    const submit = async (e: SyntheticEvent) => {
        e.preventDefault();

        await fetch(`${ADMIN_API_URL}/api/products/${id}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                title,
                image
            })
        });

        setRedirect(true);
    }

    if (redirect) {
        return <Navigate to={'/admin/products'} replace/>
    }

    return (
        <Wrapper>
            <form onSubmit={submit}>
                <div className="form-group">
                    <label>Title</label>
                    <input type="text" className="form-control" name="title"
                           value={title}
                           onChange={e => setTitle(e.target.value)}
                    />
                </div>
                <div className="form-group">
                    <label>Image</label>
                    <input type="text" className="form-control" name="image"
                           value={image}
                           onChange={e => setImage(e.target.value)}
                    />
                </div>
                <button className="btn btn-outline-secondary">Save</button>
            </form>
        </Wrapper>
    );
};

export default ProductsEdit;
